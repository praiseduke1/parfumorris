(function () {
    'use strict';

    /* ─── DOM SELECTORS ─── */
    var SELECTORS = {
        province:        '#id_province',
        city:            '#id_city',
        district:        '#id_district',
        postalCode:      '#id_postal_code',
        lat:             '#id_latitude',
        lng:             '#id_longitude',
        addressLine:     '#id_address_line, #id_shipping_address',
        rt:              '#id_rt',
        rw:              '#id_rw',
        label:           '#id_label',
        recipientName:   '#id_recipient_name',
        phone:           '#id_phone',
    };

    var els = {};
    Object.keys(SELECTORS).forEach(function (k) {
        var el = null;
        var parts = SELECTORS[k].split(',');
        for (var i = 0; i < parts.length; i++) {
            el = document.querySelector(parts[i].trim());
            if (el) break;
        }
        els[k] = el;
    });

    if (!els.province || !els.city) return;

    /* ─── CONSTANTS ─── */
    var LABEL = {
        province:   'Provinsi',
        city:       'Kota/Kabupaten',
        district:   'Kecamatan',
        postalCode: 'Kode Pos',
    };

    /* Hierarchy: each level knows its child, deeper levels, and API key */
    var CHAIN = [
        { name: 'province',   child: 'city',      deeper: ['district', 'postalCode'] },
        { name: 'city',       child: 'district',  deeper: ['postalCode'] },
        { name: 'district',   child: 'postalCode', deeper: [] },
    ];
    var CHAIN_BY_PARENT = {};
    CHAIN.forEach(function (link) { CHAIN_BY_PARENT[link.name] = link; });

    var TS_OPTIONS = {
        maxOptions: null,
        searchField: ['text'],
        sortField: [{ field: 'text', direction: 'asc' }],
        placeholder: 'Cari...',
        render: {
            no_results: function () {
                return '<div class="p-2 text-stone-400 text-sm">Tidak ditemukan</div>';
            },
            option: function (data, escape) {
                return '<div class="py-1.5 px-3 text-sm text-stone-700">' + escape(data.text) + '</div>';
            },
            item: function (data, escape) {
                return '<div class="text-sm">' + escape(data.text) + '</div>';
            },
        },
        onType: function (str) {
            if (str && str.length > 0) {
                this.dropdown.classList.add('ts-dropdown--searching');
            } else {
                this.dropdown.classList.remove('ts-dropdown--searching');
            }
        },
    };

    /* ─── STATE ─── */
    var abortControllers = {};

    /* ─── HELPERS ─── */

    function debug() {
        console.log.apply(console, ['[CASCADE]'].concat(Array.prototype.slice.call(arguments)));
    }

    /* ─── TOMSELECT MANAGEMENT ─── */

    function initTomSelect(sel) {
        if (!sel || sel.tomselect || sel.disabled) return;
        try {
            new TomSelect(sel, TS_OPTIONS);
        } catch (e) {
            debug('TomSelect init error:', e.message);
        }
    }

    function destroyTomSelect(sel) {
        if (sel && sel.tomselect) {
            try {
                sel.tomselect.destroy();
            } catch (e) {}
            delete sel.tomselect;
        }
    }

    function recreateTomSelect(sel) {
        destroyTomSelect(sel);
        if (sel && !sel.disabled && sel.options.length > 0) {
            initTomSelect(sel);
        }
    }

    /* ─── ABORT CONTROLLER ─── */

    function abortPending(key) {
        if (abortControllers[key]) {
            debug('Aborting previous request for', key);
            abortControllers[key].abort();
        }
        var controller = new AbortController();
        abortControllers[key] = controller;
        return controller;
    }

    /* ─── API FETCH ─── */

    function fetchJson(url, params, signal) {
        var query = Object.keys(params).map(function (k) {
            return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
        }).join('&');
        var fullUrl = url + '?' + query;
        debug('Fetch:', fullUrl);
        return fetch(fullUrl, { signal: signal }).then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        }).then(function (data) {
            debug('Response:', data ? data.length : 0, 'items');
            if (data && data.length > 0) {
                debug('  first item:', JSON.stringify(data[0]));
            }
            return data;
        });
    }

    /* ─── UI UPDATES ─── */

    function populateSelect(select, data, parentId) {
        if (!select) return;
        destroyTomSelect(select);
        var ph = select.getAttribute('data-placeholder') || 'Pilih...';
        select.innerHTML = '<option value="">' + ph + '</option>';
        if (data && data.length > 0) {
            data.forEach(function (item) {
                var opt = document.createElement('option');
                opt.value = item.id;
                opt.textContent = item.name || item.code;
                select.appendChild(opt);
            });
            select.disabled = false;
        } else {
            var emptyMsg = 'Tidak tersedia';
            if (parentId) {
                debug('EMPTY RESPONSE: parent ID', parentId, 'returned 0 items for', select.id);
                if (select.id.indexOf('district') !== -1 || select.id.indexOf('postal') !== -1) {
                    emptyMsg = 'Database wilayah belum lengkap';
                }
            }
            select.innerHTML = '<option value="">' + emptyMsg + '</option>';
            select.disabled = true;
        }
        recreateTomSelect(select);
    }

    function resetSelect(select) {
        if (!select) return;
        destroyTomSelect(select);
        var ph = select.getAttribute('data-placeholder') || 'Pilih...';
        select.innerHTML = '<option value="">' + ph + '</option>';
        select.disabled = true;
    }

    function setLoading(select) {
        if (!select) return;
        destroyTomSelect(select);
        select.innerHTML = '<option value="">Memuat...</option>';
        select.disabled = true;
    }

    function showError(message) {
        var container = document.querySelector('.cascade-error-container');
        if (!container) {
            var form = els.province ? els.province.closest('form') : null;
            container = form ? form.querySelector('.cascade-error-container') : null;
            if (!container) container = document.body;
        }
        var existing = container.querySelector('.cascade-error');
        if (existing) existing.remove();

        var div = document.createElement('div');
        div.className = 'cascade-error flex items-center justify-between gap-3 p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 mb-6';
        div.innerHTML = '<span>' + message + '</span>'
            + '<button type="button" class="retry-btn px-3 py-1.5 bg-rose-100 hover:bg-rose-200 text-rose-700 text-xs font-medium rounded-lg transition whitespace-nowrap">\u21BB Muat Ulang</button>';
        container.insertBefore(div, container.firstChild);

        div.querySelector('.retry-btn').addEventListener('click', function () {
            div.remove();
            if (els.province) {
                var evt = new Event('change', { bubbles: true });
                els.province.dispatchEvent(evt);
            }
        });

        setTimeout(function () {
            if (div.parentNode) div.remove();
        }, 15000);
    }

    /* ─── CORE: LOAD CHILDREN ─── */
    /*
     * loadChildren(parentName)
     * - parentName: 'province' | 'city' | 'district'
     * - Aborts previous in-flight request for this parent
     * - Resets ALL deeper selects (child, grandchild, etc.)
     * - If parent has a value, fetches child data and populates
     * - Returns a Promise that resolves when population is complete
     */

    function loadChildren(parentName) {
        var link = CHAIN_BY_PARENT[parentName];
        if (!link) return Promise.resolve();

        var parent = els[parentName];
        var child = els[link.child];
        var parentId = parent ? parent.value : '';

        debug(LABEL[parentName], 'changed → ID:', parentId || '(empty)');

        /* Reset ALL deeper selects (including child) immediately */
        var allDescendants = [link.child].concat(link.deeper);
        allDescendants.forEach(function (name) {
            var el = els[name];
            if (name === link.child) {
                setLoading(el);
            } else {
                resetSelect(el);
            }
        });

        if (!parentId) {
            return Promise.resolve();
        }

        var url = parent.getAttribute('data-url');
        if (!url) {
            debug('ERROR: no data-url on', LABEL[parentName], 'element');
            if (child) {
                child.innerHTML = '<option value="">Kesalahan konfigurasi</option>';
                child.disabled = false;
            }
            return Promise.resolve();
        }

        /* Abort previous & create new AbortController */
        var controller = abortPending(parentName);
        var params = {};
        params[parentName + '_id'] = parentId;

        debug('  → Loading', LABEL[link.child], 'from', url, 'with', JSON.stringify(params));

        return fetchJson(url, params, controller.signal).then(function (data) {
            /* Stale-response guard: if a newer request started, discard */
            if (abortControllers[parentName] !== controller) {
                debug('  ↻ Ignoring stale response for', LABEL[parentName]);
                return;
            }
            debug('  ✓', LABEL[link.child], 'loaded:', data ? data.length : 0, 'items');
            if (!data || data.length === 0) {
                debug('  ⚠ EMPTY:', LABEL[parentName], 'ID', parentId, 'has zero', LABEL[link.child], 'in database');
                debug('  ⚠ Cause: database wilayah belum memiliki data', LABEL[link.child], 'untuk', LABEL[parentName], 'ini');
            }
            populateSelect(child, data, parentId);
            /* Safety: re-reset deeper (grandchild) selects in case they were populated */
            link.deeper.forEach(function (name) {
                resetSelect(els[name]);
            });
        }).catch(function (err) {
            if (err.name === 'AbortError') {
                debug('  ⊘ Request aborted for', LABEL[parentName]);
                return;
            }
            debug('  ✗ Fetch error:', err.message);
            if (child) {
                child.innerHTML = '<option value="">Gagal memuat</option>';
                child.disabled = false;
            }
            showError('Gagal mengambil data ' + (LABEL[link.child] || '').toLowerCase() + '. Silakan coba lagi.');
        });
    }

    /* ─── BIND CHANGE EVENTS ─── */

    CHAIN.forEach(function (link) {
        var el = els[link.name];
        if (!el) return;
        el.addEventListener('change', function () {
            loadChildren(link.name);
        });
    });

    /* ─── INITIALIZATION ─── */

    function initSelects() {
        ['province', 'city', 'district', 'postalCode'].forEach(function (k) {
            var el = els[k];
            if (!el) return;
            if (el.value) {
                el.disabled = false;
                recreateTomSelect(el);
            }
        });
    }

    /*
     * loadInitialChain()
     * Called on page load when editing an existing address.
     * Sequentially loads districts then postal codes if city/district have values.
     * SKIPS if the child select already has options (server-rendered).
     */
    function loadInitialChain() {
        var provinceVal = els.province ? els.province.value : '';
        if (!provinceVal) return;

        /* If city already has server-rendered options in edit mode, skip province→city load */
        if (els.city && els.city.options.length > 1) {
            debug('Initial chain: city already has options, skipping province→city');
            /* Still need to load deeper if they have selected values */
            if (els.city.value) {
                if (els.district && els.district.options.length <= 1) {
                    loadChildren('city').then(function () {
                        if (els.district && els.district.value && els.postalCode && els.postalCode.options.length <= 1) {
                            loadChildren('district');
                        }
                    });
                } else if (els.district && els.district.value) {
                    if (els.postalCode && els.postalCode.options.length <= 1) {
                        loadChildren('district');
                    }
                }
            }
            return;
        }

        debug('Initial chain load: province ID =', provinceVal);

        loadChildren('province').then(function () {
            if (!els.city || els.city.disabled) return;
            var cityVal = els.city.value;
            if (!cityVal) return;
            debug('Initial chain: city ID =', cityVal);
            return loadChildren('city');
        }).then(function () {
            if (!els.district || els.district.disabled) return;
            var districtVal = els.district.value;
            if (!districtVal) return;
            debug('Initial chain: district ID =', districtVal);
            return loadChildren('district');
        }).catch(function (err) {
            debug('Initial chain error:', err.message);
        });
    }

    initSelects();
    loadInitialChain();

    /* ─── SET SELECT VALUE (programmatic, no event) ─── */

    function setSelectValue(select, value) {
        if (!select) return;
        destroyTomSelect(select);
        select.value = value;
        select.disabled = false;
        recreateTomSelect(select);
    }

    /* ─── SELECT SAVED ADDRESS ─── */

    function selectAddress(addressId) {
        var card = document.querySelector('.address-card[data-id="' + addressId + '"]');
        if (!card) return;

        var address     = card.getAttribute('data-address') || '';
        var provinceId  = card.getAttribute('data-province-id') || '';
        var cityId      = card.getAttribute('data-city-id') || '';
        var districtId  = card.getAttribute('data-district-id') || '';
        var postalCodeId = card.getAttribute('data-postalcode-id') || '';

        debug('selectAddress #' + addressId,
              'province:', provinceId,
              'city:', cityId,
              'district:', districtId,
              'postalCode:', postalCodeId);

        if (els.addressLine) els.addressLine.value = address;

        /* Highlight card */
        document.querySelectorAll('.address-card').forEach(function (c) {
            c.classList.remove('border-amber-500', 'bg-amber-50/50');
            c.classList.add('border-stone-200', 'bg-white');
        });
        card.classList.remove('border-stone-200', 'bg-white');
        card.classList.add('border-amber-500', 'bg-amber-50/50');

        var rn = card.getAttribute('data-recipient') || '';
        if (rn && els.recipientName) els.recipientName.value = rn;
        var pv = card.getAttribute('data-phone') || '';
        if (pv && els.phone) els.phone.value = pv;

        if (!provinceId) return;

        /* Abort all pending requests */
        Object.keys(abortControllers).forEach(function (key) {
            abortControllers[key].abort();
        });
        abortControllers = {};

        /* Reset all selects below province */
        resetSelect(els.city);
        resetSelect(els.district);
        resetSelect(els.postalCode);

        /* Set province value (no event) */
        setSelectValue(els.province, provinceId);

        /* Chain: province→city, city→district, district→postalCode */
        loadChildren('province').then(function () {
            if (!els.city || els.city.disabled || !cityId) return;
            setSelectValue(els.city, cityId);
            return loadChildren('city');
        }).then(function () {
            if (!els.district || els.district.disabled || !districtId) return;
            setSelectValue(els.district, districtId);
            return loadChildren('district');
        }).then(function () {
            if (els.postalCode && !els.postalCode.disabled && postalCodeId) {
                setSelectValue(els.postalCode, postalCodeId);
                recreateTomSelect(els.postalCode);
            }
        }).catch(function (err) {
            debug('selectAddress chain error:', err.message);
        });
    }

    window.selectAddress = selectAddress;

    /* ─── GEOLOCATION ─── */

    function useCurrentLocation() {
        if (!navigator.geolocation) {
            showError('Geolokasi tidak didukung oleh browser Anda.');
            return;
        }

        var btn = document.getElementById('geoLocationBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Mendeteksi lokasi...';
        }

        navigator.geolocation.getCurrentPosition(function (pos) {
            var lat = pos.coords.latitude.toFixed(6);
            var lng = pos.coords.longitude.toFixed(6);

            if (els.lat) els.lat.value = lat;
            if (els.lng) els.lng.value = lng;

            fetch(
                'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat='
                + lat + '&lon=' + lng + '&accept-language=id',
                { headers: { 'User-Agent': 'ParfuMoray/1.0' } }
            ).then(function (r) { return r.json(); }).then(function (data) {
                var addr = data.display_name || '';
                var addressData = data.address || {};

                if (els.addressLine && addr) {
                    els.addressLine.value = addr.split(',').slice(0, 3).join(',');
                }

                var provinceName = addressData.state || addressData.province || '';
                var cityName = addressData.city || addressData.county || addressData.municipality || '';
                var districtName = addressData.suburb || addressData.town || addressData.village || addressData.district || '';

                function findAndSelect(select, name, nextFn) {
                    if (!select || !name) { if (nextFn) nextFn(); return; }
                    var normalized = name.toLowerCase().trim();
                    var waitMax = 100;
                    (function poll() {
                        if (!select.disabled && select.options.length > 1) {
                            var bestOpt = null;
                            var bestScore = 0;
                            for (var i = 0; i < select.options.length; i++) {
                                var opt = select.options[i];
                                if (!opt.value) continue;
                                var optName = (opt.textContent || '').toLowerCase().trim();
                                var score = 0;
                                if (optName === normalized) score = 100;
                                else if (optName.indexOf(normalized) !== -1) score = 50;
                                else if (normalized.indexOf(optName) !== -1) score = 30;
                                if (score > bestScore) { bestScore = score; bestOpt = opt; }
                            }
                            if (bestOpt) {
                                setSelectValue(select, bestOpt.value);
                                debug('Geolocation: matched', select.id, '→', bestOpt.value, '(' + bestOpt.textContent + ')');
                                var evt = new Event('change', { bubbles: true });
                                select.dispatchEvent(evt);
                            } else {
                                debug('Geolocation: no match for', select.id, 'looking for', normalized);
                            }
                            if (nextFn) nextFn();
                            return;
                        }
                        if (waitMax > 0) { waitMax--; setTimeout(poll, 80); }
                        else { if (nextFn) nextFn(); }
                    })();
                }

                findAndSelect(els.province, provinceName, function () {
                    findAndSelect(els.city, cityName, function () {
                        findAndSelect(els.district, districtName, null);
                    });
                });
            }).catch(function (err) {
                debug('Geolocation reverse geocode error:', err.message);
            }).finally(function () {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg> Gunakan Lokasi Saya';
                }
            });
        }, function (err) {
            var msg = 'Gagal mendapatkan lokasi.';
            if (err.code === 1) msg = 'Akses lokasi ditolak. Izinkan akses lokasi di pengaturan browser.';
            else if (err.code === 2) msg = 'Posisi tidak tersedia. Coba lagi.';
            else if (err.code === 3) msg = 'Waktu permintaan lokasi habis. Coba lagi.';
            showError(msg);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg> Gunakan Lokasi Saya';
            }
        }, {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 60000,
        });
    }

    var geoBtn = document.getElementById('geoLocationBtn');
    if (geoBtn) {
        geoBtn.addEventListener('click', function (e) {
            e.preventDefault();
            useCurrentLocation();
        });
    }

    var advancedToggle = document.getElementById('advancedToggle');
    var advancedContent = document.getElementById('advancedContent');
    if (advancedToggle && advancedContent) {
        var chevron = advancedToggle.querySelector('.chevron-icon');
        advancedToggle.addEventListener('click', function (e) {
            e.preventDefault();
            var isHidden = advancedContent.classList.contains('hidden');
            advancedContent.classList.toggle('hidden');
            if (chevron) chevron.classList.toggle('rotate-180');
            advancedToggle.setAttribute('aria-expanded', isHidden);
        });
    }

})();

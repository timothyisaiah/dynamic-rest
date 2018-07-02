window.drest = {};

$(document).ready(function() {
    function DRESTForm(_form) {
        var form = this;
        this.$form = $(_form);
        this.$fields = this.$form.find('.drest-field');
        this.disabled = this.$form.hasClass('drest-form--readonly');

        this.toggleDisabled = function() {
            if (form.disabled) {
                form.$form.removeClass('drest-form--readonly');
            } else {
                form.$form.addClass('drest-form--readonly');
            }
            form.disabled = !form.disabled;
            form.$fields.each(function() {
                var $f = $(this);
                var f = $f[0];
                f = f.DRESTField;
                if (f) {
                    f.toggleDisabled()
                }
            });
        };
        this.$form.addClass('drest-form--js');
        this.$form[0].DRESTForm = this;
    }

    function DRESTField(args) {
        var field = this;
        field.id = args.id;
        var $field = field.$field = $('#' + field.id);
        var $input = field.$input = $('#' + field.id + '-input');
        var $form = field.$form = $field.closest('.drest-form');
        var $label = field.$field.find('label, .drest-field__label');
        var $select2;
        field.controls = args.controls;
        field.disabled = !$form.length || $form.hasClass('drest-form--readonly');
        field.readOnly = args.readOnly;
        field.helpTextShort = args.helpTextShort;
        field.helpText = args.helpText;
        field.writeOnly = args.writeOnly;
        field.required = args.required;
        field.initial = field.value = args.value;
        field.label = args.label;
        field.type = args.type;
        field.many = args.many || field.type === 'list';
        field.relation = args.relation;

        if (field.helpText) {
            $label.addClass('drest-tooltip');
            $label[0].title = field.helpText;
            $label.attr('data-tippy-trigger', 'click');
            tippy($label);
        }
        this.isEmpty = function(value) {
            if (this.type === 'relation' || this.type === 'list') {
                if (this.many) {
                    return !value.length;
                }
                else {
                    return !value;
                }
            } else {
                return typeof value === 'undefined' || value === '' || value === null;
            }
        }
        this.hasChanged = function() {
            return this.value != this.initial;
        }
        this.enable = function() {
            this.$field.removeClass('drest-field--disabled');
            this.$input[0].disabled = false;
            this.$field.find('.mdc-text-field').removeClass('mdc-text-field--disabled');
        }
        this.disable = function() {
            this.$field.addClass('drest-field--disabled');
            this.$input[0].disabled = true;
            this.$field.find('.mdc-text-field').addClass('mdc-text-field--disabled');
        }
        this.toggleDisabled = function() {
            var $field = this.$field;
            var $input = this.$input;
            if (this.disabled) {
                // enable if not readOnly
                if (!this.readOnly) {
                    this.enable();
                }
            } else {
                // disable
                this.disable();
            }
            this.disabled = !this.disabled;
        }
        this.reset = function(value) {
            this.initial = this.value = value;
            this.$input.val(value);
        }

        // setup dependents and listeners
        if (field.type === 'list') {
            var value = field.value;
            var $select2 = $input;
            if (value) {
                for (var v in value) {
                    if (value.hasOwnProperty(v)) {
                        $input.append(
                            '<option selected="selected">' + value[v] + '</option>'
                        );
                    }
                }
            }
            $select2.select2({
                tags: true,
                placeholder: field.label,
                theme: 'material',
                minimumInputLength: 1,
                language: {
                    inputTooShort: function() {
                        return field.helpTextShort || "Start typing";
                    }
                },
                dropdownParent: $field
            });
        } else if (field.type === 'relation') {
            if (field.relation.image) {
            } else {
                var perPage = 25;
                var value = field.value;
                var selected;
                var initials;
                // get field/serializer info
                var nameField = field.relation.nameField;
                var searchKey = field.relation.searchKey;
                var pkField = field.relation.pkField;
                var resourceName = field.relation.resourceName;
                var pluralName = field.relation.pluralName;
                var url = field.relation.url;
                var includes = [pkField];
                if (pkField !== nameField) {
                    includes.push(nameField);
                }
                if (field.many) {
                    selected = [];
                    initials = [];
                    if (value) {
                        for (var v in value) {
                            if (value.hasOwnProperty(v)) {
                                v = value[v];
                                initials.push({
                                    id: v.id,
                                    text: v[nameField],
                                    name: v[nameField],
                                    selected: true
                                });
                                selected.push(v.id);
                            }
                        }
                    }
                } else {
                    if (value && value.id) {
                        initials = [{
                            id: value.id,
                            text: value[nameField],
                            name: value[nameField],
                            selected: true
                        }];
                        selected = value.id;
                    } else {
                        initials = [];
                        selected = null;
                    }
                }
                var $select2 = $input;
                var select2 = $select2[0];
                var placeholder = field.many ? field.label : {
                    id: "",
                    placeholder: field.label
                };
                $select2.select2({
                    data: initials,
                    dropdownParent: $field,
                    language: {
                        inputTooShort: function() {
                            return field.helpTextShort
                        }
                    },
                    width: 'resolve',
                    theme: 'material',
                    placeholder: placeholder,
                    allowClear: !field.required,
                    ajax: {
                        url: url,
                        dataType: "json",
                        delay: 250,
                        data: function(params) {
                          var result = {
                            page: params.page,
                            per_page: perPage,
                          };
                          result[searchKey] = params.term;
                          result['exclude[]'] = '*';
                          result['include[]'] = includes;
                          return result;
                        },
                        processResults: function(data, params) {
                          params.page = params.page || 1;
                          var meta = data.meta;
                          var result = {
                            results: data[pluralName],
                            pagination: {
                              more: meta ? meta.page < meta.total_pages : false
                            }
                          };
                          return result;
                        }
                    },
                    escapeMarkup: function(markup) {
                        return markup;
                    },
                    templateResult: function(item) {
                        if (item.placeholder) return item.placeholder;
                        if (nameField == 'pk') {
                            return item.links ? item.links.self : item.id;
                        }
                        return item[nameField];
                    },
                    templateSelection: function(item) {
                        if (item.placeholder) return item.placeholder;
                        if (nameField == 'pk') {
                            return item.links ? item.links.self : item.id;
                        }
                        return item[nameField];
                    },
                    minimumInputLength: 1,
                });
                $select2.val(selected);
                if (field.many) {
                    $field.find('.select2-selection__choice').addClass('drest--clickable').on('click.drest-field', function() {
                        if (field.disabled && !field.isEmpty(field.value)) {
                            var $this = $(this);
                            var name = $this.attr('title');
                            var group = $this.closest('.select2-seletion__rendered');
                            var value = field.value;

                            for (var i = 0; i < value.length; i++) {
                                if (value[i][nameField] == name) {
                                    window.spin();
                                    window.location = url + '/' + value[i].id;
                                }
                            }
                        }
                    });
                } else {
                    $field.find('.select2-selection--single').addClass('drest--clickable').on('click.drest-field', function() {
                        if (field.disabled && !field.isEmpty(field.value)) {
                            window.spin();
                            window.location = url + '/' + field.value.id;
                        }
                    });
                }
            }
        } else if (field.type === 'boolean') {
            $input.on('click', function() {
                var $this = $(this);
                $this.attr('value', $this.is(':checked')).trigger('change');
            });
            if (field.value === null){
                $input[0].indeterminate = true;
                $input.attr('value', null);
            } else {
                $input.attr('value', $input.is(':checked'));
            }
        } else if (field.type === 'file') {
            $input.dropify();
            $field.find('.dropify-render').append(
                '<img src="' + field.value + '">'
            );
        }
        if ($select2) {
            $select2.on('select2:open', function(e){
                $field.addClass('drest-field--focused');
            });
            $select2.on('select2:close', function(e){
                $field.removeClass('drest-field--focused');
                $field.removeClass('drest-field--invalid');
            });
            $select2.data('select2').on('results:message', function() {
                this.dropdown._resizeDropdown();
                this.dropdown._positionDropdown();
            });
        }

        if (this.disabled) {
            this.disable();
        }
        $input.on('change', function() {
            var value = $input.val();
            if (field.isEmpty(value)) {
                $field.removeClass('drest-field--selected');
            } else {
                $field.addClass('drest-field--selected');
            }
            if (this.controls) {
                var show = controls[value || ''];
                this.$form.find('.drest-field')
                .each(function() {
                    var $f = $(this);
                    var f = $f[0].DRESTField;
                    if (f.disabled) {
                        return;
                    }
                    var name = f.name;
                    if (!show || show.length === 0) {
                        $f.show();
                    } else {
                        if (show.indexOf(name) > -1)  {
                            $f.show();
                        } else {
                            $f.hide();
                        }
                    }
                });
            }
            field.value = value;
        });
        if (!field.isEmpty(field.value)) {
            $field.addClass('drest-field--selected');
        }
        $field[0].DRESTField = this;
        $field.addClass('drest-field--js');
        window.$field = $field[0];
    }

    window.drest = {
        DRESTForm: DRESTForm,
        DRESTField: DRESTField
    };

    var formId = 0;
    $('.drest-form').each(function() {
        var form = new DRESTForm($(this)[0]);
    });

    function replaceDocument(docString) {
      var doc = document.open("text/html");

      doc.write(docString);
      doc.close();
    }

    function doAjaxSubmit(e) {
      var form = $(this);
      var btn = $(this.clk);
      var method = (
        btn.data('method') ||
        form.data('method') ||
        form.attr('method') || 'GET'
      ).toUpperCase();

      if (method === 'GET') {
        // GET requests can always use standard form submits.
        return;
      }

      var contentType =
        form.find('input[data-override="content-type"]').val() ||
        form.find('select[data-override="content-type"] option:selected').text();

      if (method === 'POST' && !contentType) {
        // POST requests can use standard form submits, unless we have
        // overridden the content type.
        return;
      }

      // At this point we need to make an AJAX form submission.
      e.preventDefault();

      var url = form.attr('action');
      var data;

      if (contentType) {
        data = form.find('[data-override="content"]').val() || ''

        if (contentType === 'multipart/form-data') {
          // We need to add a boundary parameter to the header
          // We assume the first valid-looking boundary line in the body is correct
          // regex is from RFC 2046 appendix A
          var boundaryCharNoSpace = "0-9A-Z'()+_,-./:=?";
          var boundaryChar = boundaryCharNoSpace + ' ';
          var re = new RegExp('^--([' + boundaryChar + ']{0,69}[' + boundaryCharNoSpace + '])[\\s]*?$', 'im');
          var boundary = data.match(re);
          if (boundary !== null) {
            contentType += '; boundary="' + boundary[1] + '"';
          }
          // Fix textarea.value EOL normalisation (multipart/form-data should use CR+NL, not NL)
          data = data.replace(/\n/g, '\r\n');
        }
      } else {
        contentType = form.attr('enctype') || form.attr('encoding')

        if (contentType === 'multipart/form-data') {
          if (!window.FormData) {
            alert('Your browser does not support AJAX multipart form submissions');
            return;
          }

          // Use the FormData API and allow the content type to be set automatically,
          // so it includes the boundary string.
          // See https://developer.mozilla.org/en-US/docs/Web/API/FormData/Using_FormData_Objects
          contentType = false;
          data = new FormData(form[0]);
        } else {
          contentType = 'application/x-www-form-urlencoded; charset=UTF-8'
          data = form.serialize();
        }
      }

      var ret = $.ajax({
        url: url,
        method: method,
        data: data,
        contentType: contentType,
        processData: false,
        headers: {
          'Accept': 'text/html; q=1.0, */*'
        },
      });

      ret.always(function(data, textStatus, jqXHR) {
        // History API no supported, so redirect.
            if (textStatus != 'success') {
              jqXHR = data;
            } else {
                window.location = url;
            }

            var responseContentType = jqXHR.getResponseHeader("content-type") || "";

            if (responseContentType.toLowerCase().indexOf('text/html') === 0) {
              replaceDocument(jqXHR.responseText);

              try {
                // Modify the location and scroll to top, as if after page load.
                history.replaceState({}, '', url);
                scroll(0, 0);
              } catch (err) {
                // History API not supported, so redirect.
                window.location = url;
              }
            } else {
              // Not HTML content. We can't open this directly, so redirect.
              window.location = url;
            }

      });

      return ret;
    }

    function captureSubmittingElement(e) {
      var target = e.target;
      var form = this;

      form.clk = target;
    }

    $.fn.ajaxForm = function() {
      var options = {}

      return this
        .unbind('submit.form-plugin  click.form-plugin')
        .bind('submit.form-plugin', options, doAjaxSubmit)
        .bind('click.form-plugin', options, captureSubmittingElement);
    };
});


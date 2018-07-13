window.drest = {};
function DRESTApp(config) {
    this.getMainForm = function() {
        if (this._mainForm === null) {
            var form = this.$mainForm[0];
            form = form ? form.DRESTForm : null;
            this._mainForm = form;
        }
        return this._mainForm;
    };
    this.enableEdit = function() {
        var form = this.getMainForm();
        this.$title.html(this.editTitle);
        this.$header.addClass('drest-app--editing');
        this.$fab.addClass('drest-app--editing');
        form.toggleDisabled();
        this.editing = true;
    };
    this.disableEdit = function() {
        var form = this.getMainForm();
        this.$title.html(this.originalTitle);
        this.$header.removeClass('drest-app--editing');
        this.$fab.removeClass('drest-app--editing');
        form.toggleDisabled();
        this.editing = false;
    };
    this.onEditFailed = function() {
        this.submitting = false;
        this.$header.removeClass('drest-app--submitting');
        this.$fab.removeClass('drest-app--submitting');
    };
    this.onEditNoop = function() {
        this.submitting = false;
        this.$header.removeClass('drest-app--submitting');
        this.$fab.removeClass('drest-app--submitting');
        this.disableEdit();
    };
    this.onEditOk = function() {
        this.submitting = false;
        this.$fab.removeClass('drest-app--submitting');
        this.$header.removeClass('drest-app--submitting');

        this.disableEdit();
    };
    this.save = function() {
        if (this.submitting) {
            return;
        }
        // save primary record
        this.$header.addClass('drest-app--submitting');
        this.submitting = true;
        this.getMainForm().submit();
    };
    this.back = function() {
        if (this.submitting) {
            return;
        }
        var form = this.getMainForm();
        if (form.hasChanged()) {
            form.reset();
        }
        this.disableEdit();
    };
    this.onLoad = function() {
        var config = this.config;
        this.$mainForm = $('#' + config.mainFormId);
        var $header = this.$header = $('#' + config.headerId);
        this.$fab = $('#' + config.fabId);
        this.$drawer = $('#' + config.drawerId);
        this.$cancelButton = $header.find('.drest-app__cancel-button');
        this.$moreButton = $header.find('.drest-app__more-button');
        this.$searchButton = $header.find('.drest-app__search-button');
        this.$saveButton = $header.find('.drest-app__save-button');
        this.$spinner = $header.find('drest-app__spinner');
        this.$navButton = $header.find('.drest-app__nav-button');
        this.$backButton = $header.find('.drest-app__back-button');
        this.$title = $header.find('.drest-app__title');
        this.$moreMenu = $header.find('.drest-app__more-menu');
        this.originalTitle = this.$title.html();
        this.editTitle = '<span class="mdi mdi-pencil"/>  Editing ' + config.resourceName;
        if (this.$drawer.length) {
            this.drawer = new mdc.drawer.MDCTemporaryDrawer(this.$drawer[0]);
        }
        if (this.$moreMenu.length) {
            this.moreMenu = new mdc.menu.MDCMenu(this.$moreMenu[0]);
            this.$moreButton.on('click.drest', function() {
                this.moreMenu.open = !this.moreMenu.open;
            }.bind(this));
        }
        this.$navButton.on('click', function() {
            this.drawer.open = true;
        }.bind(this));

        this.$mainForm.on('drest-form:submit-succeeded', this.onEditOk.bind(this));
        this.$mainForm.on('drest-form:submit-failed', this.onEditFailed.bind(this));
        this.$mainForm.on('drest-form:submit-noop', this.onEditNoop.bind(this));
        if (this.$fab.hasClass('drest-fab--edit')) {
            this.$fab.on('click.drest', this.enableEdit.bind(this));
        }
        this.$saveButton.on('click.drest', this.save.bind(this));
        this.$backButton.on('click.drest', this.back.bind(this));
    };

    this._mainForm = null;
    this.editing = false;
    this.submitting = false;
    this.config = config;

    $(this.onLoad.bind(this));
}

window.drest = {
    DRESTApp: DRESTApp
};

$(document).ready(function() {
    Dropify.prototype.isTouchDevice = function() { return false; }
    Dropify.prototype.getFileType = function() {
        return this.file.name.split('.').pop().split('?').shift().toLowerCase();
    };
    function DRESTForm(_form) {
        this.submit = function() {
            return this.$form.submit();
        };
        this.getFields = function() {
            if (this._fields === null) {
                var fields = this.$fields.map(function() {
                    return this.DRESTField;
                });
                if (fields.length === this.$fields.length) {
                    this._fields = fields;
                } else {
                    console.log(
                        'warning: form field length mismatch',
                        fields.map(function() { return this.name; }),
                        fields.length,
                        this.$fields.length
                    );
                    return fields;
                }
            }
            return this._fields;
        };
        this.hasFiles = function(changedOnly) {
            var fields = this.getFields();
            for (var i=0; i<fields.length; i++) {
                var field = fields[i];
                if (field.type !== 'file') {
                    continue;
                }
                if (changedOnly && !field.hasChanged()) {
                    continue;
                }
                return true;
            }
        };
        this.getFieldsByName = function() {
            if (this._fieldsByName === null) {
                var fields = this.getFields();
                var result = {};
                for (var i = 0; i < fields.length; i++) {
                    var f = fields[i];
                    result[f.name] = f;
                }
                this._fieldsByName = result;
            }
            return this._fieldsByName;
        };
        this.toggleDisabled = function() {
            if (this.disabled) {
                this.$form.removeClass('drest-form--readonly');
            } else {
                this.$form.addClass('drest-form--readonly');
            }
            this.disabled = !this.disabled;
            this.getFields().each(function() {
                this.toggleDisabled();
            });
        };
        this.reset = function() {
            this.getFields().each(function() {
                if (this.hasChanged()) {
                    this.reset(this.initial);
                }
            });
        };
        this.hasChanged = function() {
            var fields = this.getFields();
            for (var i=0; i<fields.length; i++) {
                var field = fields[i];
                if (field.hasChanged()) {
                    return true;
                }
            }
            return false;
        };
        this.onSubmit = function(e) {
              var form = this.$form;
              var method = (form.data('method') || form.attr('method') || 'GET').toUpperCase();

              if (method === 'GET' || method === 'POST') {
                return;
              }

              e.preventDefault();

              var url = form.attr('action');
              var data;
              var multipart = false;
              var contentType = 'application/json';
              // by default, try using JSON
              if (this.hasFiles(method === 'PATCH')) {
                  // if we need to save files, use multipart/form-data
                  contentType = false;
                  multipart = true;
              }
              if (method === 'DELETE') {
                  data = null;
              } else {
                  if (multipart) {
                      data = new FormData();
                  } else {
                      data = {};
                  }
                  var fields = this.getFields();
                  var anyChanges = false;
                  for (var i=0; i<fields.length; i++) {
                    var f = fields[i];
                    if (method === 'PUT' || f.hasChanged()) {
                        var val = f.getSubmitValue();
                        if (multipart) {
                            // convert null to empty string
                            if (val === null) {
                                val = "";
                            }
                            if ($.isArray(val)) {
                                for (var j=0; j<val.length; j++) {
                                    data.append(f.name, val[j]);
                                }
                            } else {
                                data.append(f.name, val);
                            }
                        } else {
                            data[f.name] = val;
                        }
                        anyChanges = true;
                    }
                  }
                  if (!anyChanges) {
                    // no changes to save -> noop
                    form.trigger('drest-form:submit-noop');
                    return;
                  }
                  if (!multipart) {
                    data = JSON.stringify(data);
                  }
              }

              form.trigger('drest-form:submitting');
              return $.ajax({
                url: url,
                method: method,
                data: data,
                contentType: contentType,
                processData: false,
                dataType: 'json',
                headers: {
                  'Accept': 'application/json'
                },
              }).done(function(data, textStatus, jqXHR) {
                    if (method === 'DELETE') {
                        data = null;
                    } else {
                        for (var x in data) {
                            if (data.hasOwnProperty(x)) {
                                data = data[x];
                                break;
                            }
                        }
                    }
                    form.trigger('drest-form:submit-succeeded', [{
                        'status': jqXHR.status,
                        'data': data,
                    }]);
              }).fail(function(jqXHR) {
                    form.trigger('drest-form:submit-failed', [{
                        'error': jqXHR.responseJSON,
                        'status': jqXHR.status,
                    }]);
              });
        };
        this.onSubmitFailed = function(e, response) {
            var errors = response.error || {};
            var fields = this.getFieldsByName();
            for (var key in fields) {
              if (fields.hasOwnProperty(key)) {
                var error = errors[key];
                var f = fields[key];
                if (error) {
                    f.setError(error);
                } else {
                    f.clearError();
                }
              }
            }
        };
        this.onSubmitSucceeded = function(e, response) {
            var data = response.data;
            var fields = this.getFields();
            for (var i=fields.length-1; i>=0; i--) {
                var field = fields[i];
                var name = field.name;
                var d = data[name];
                if (typeof d !== 'undefined') {
                    field.reset(d);
                } else {
                    field.clearError();
                }
            }
        };

        var form = this;
        this._fields = null;
        this._fieldsByName = null;

        this.$form = $(_form);
        this.$form.addClass('drest-form--js');

        this.$fields = this.$form.find('.drest-field');
        this.disabled = this.$form.hasClass('drest-form--readonly');
        this.$form.on('drest-form:submit-failed', this.onSubmitFailed.bind(this));
        this.$form.on('drest-form:submit-succeeded', this.onSubmitSucceeded.bind(this));
        this.$form.off('submit.drest-form').on('submit.drest-form', this.onSubmit.bind(this));
        this.$form[0].DRESTForm = this;
    }

    function DRESTField(args) {
        this.getSubmitValue = function() {
            if (this.type === 'file') {
                var input = this.$input[0];
                var files = input.files;
                return (files && files.length) ? files[0] : null;
            }
            return this.value;
        };
        this.getInputValue = function() {
            var val = this.$input.val();
            if (val === null && this.many) {
                // replace null with empty list for
                // any "many" field
                val = [];
            }
            if (this.type === 'boolean') {
                if (val === 'false') {
                    val = false;
                } else if (val === 'true') {
                    val = true;
                }
            }
            return val;
        };
        this.getForm = function() {
            if (this._form === null) {
                var form = this.$form[0];
                form = form ? form.DRESTForm : null;
                this._form = form;
            }
            return this._form;
        };
        this.isEmpty = function(value) {
            if (value === null || typeof value === 'undefined' || value === '') {
                return true;
            }
            if (this.many && value) {
                return value.length === 0;
            }
            return false;
        };
        this.equal = function(a, b) {
            if ($.isArray(a) || $.isPlainObject(a)) {
                return JSON.stringify(a) === JSON.stringify(b);
            } else {
                return a == b;
            }
        };
        this.hasChanged = function() {
            return !this.equal(this.initial, this.value);
        };
        this.enable = function() {
            this.$field.removeClass('drest-field--disabled');
            this.$input[0].disabled = false;
            this.$textField.removeClass('mdc-text-field--disabled');
            this.$select.removeClass('mdc-select--disabled');
            this.disabled = false;
        };
        this.addSelect2ChoiceHandlers = function() {
            var $choice;
            var field = this;
            var relation = this.type === 'relation';
            var url = relation ? this.relation.url : null;

            var onClick = function(e) {
                var $el = $(this);
                var url = $el.data('url');
                if (url && $el.closest('.drest-form').hasClass('drest-form--readonly')) {
                    window.location = url;
                }
            };
            var onChoiceClick = function(e) {
                if (field.disabled) {
                    (onClick.bind(this))(e);
                } else {
                    field.$field.addClass('drest-field--focused');
                    var $search = field.$input.find('.select2-search--inline .select2-search__field');
                    $search.focus();
                }
            };
            if (this.many) {
                var $choices = this.$field.find('.select2-selection__choice');
                for (var i = 0; i < $choices.length; i++) {
                    $choice = $($choices[i]);
                    var v = this.value[i];
                    var t = $choice.attr('title');
                    if ($choice.text().indexOf(t) === -1) {
                        // fix select2 bug where selection text is not set

                        $choice.html(
                            '<span class="select2-selection__choice__remove">&times;</span>' + t
                        );
                    }
                    $choice.addClass('drest--clickable');
                    if (url) {
                        $choice.attr('data-url', url + '/' + v);
                    }
                    $choice.off('click.drest-field').on('click.drest-field', onChoiceClick);
                }
            } else {
                if (relation) {
                    $choice = this.$field.find('.select2-selection__rendered');
                    if (!this.isEmpty(this.value)) {
                        $choice.addClass('drest--clickable');
                        if (url) {
                            $choice.attr('data-url', url + '/' + this.value);
                        }
                        $choice.off('click.drest-field').on('click.drest-field', onClick);
                    }
                }
            }
        };
        this.disable = function() {
            var field = this;
            this.$field.addClass('drest-field--disabled');
            this.$input[0].disabled = true;
            this.$textField.addClass('mdc-text-field--disabled');
            this.$select.addClass('mdc-select--disabled');
            this.disabled = true;

            if (this.type === 'relation' || this.type === 'list') {
                this.addSelect2ChoiceHandlers();
            }
        };
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
        };
        this.reset = function(value) {
            if (!this.equal(this.value, value)) {
                if (this.isEmpty(value)) {
                    this.$field.removeClass('drest-field--selected');
                    this.$label.removeClass('mdc-floating-label--float-above');
                } else {
                    this.$field.addClass('drest-field--selected');
                    if (this.$label.hasClass('mdc-floating-label')) {
                        this.$label.addClass('mdc-floating-label--float-above');
                    }
                }

                if (this.type === 'file') {
                    var d = this.$input.data('dropify');
                    d.resetPreview();
                    if (value) {
                        d.file.name = d.cleanFilename(value);
                        d.setPreview(d.isImage(), value);
                    }
                } else if (this.type === 'relation') {
                    if (this.relation.image) {
                        // noop
                    } else {
                        this.$input.val(value).trigger('change');
                    }
                } else if (this.type === 'list') {
                    // make sure the select has all of the options required
                    for (var i=0; i<value.length; i++) {
                        var v = value[i];

                        if (!this.$input.find('option[value="' + v + '"]').length) {
                            this.$input.append(
                                '<option value="' + v + '">' + v + '</option>'
                            );
                        }
                        this.$input.val(value).trigger('change');
                    }
                    this.$input.val(value).trigger('change');
                } else if (this.type === 'boolean') {
                    if (value === null) {
                        this.$input[0].indeterminate = true;
                        this.$input[0].checked = false;
                    } else {
                        this.$input[0].indeterminate = false;
                        this.$input[0].checked = !!value;
                    }
                    this.$input.val(value);
                } else {
                    this.$input.val(value);
                }
                this.value = value;
            }
            this.initial = value;
            this.$field.removeClass('drest-field--changed');
            this.clearError();
            if (this.type === 'relation' || this.type === 'list') {
                this.addSelect2ChoiceHandlers();
            }
        };
        this.setError = function(errors) {
            this.$field.addClass('drest-field--invalid');
            this.$textField.addClass('mdc-text-field--invalid');
            this.$select.addClass('mdc-text-field--invalid');
            this.$helper.addClass('mdc-text-field-helper-text--persistent').html(errors[0]);
        };
        this.clearError = function() {
            this.$field.removeClass('drest-field--invalid');
            this.$textField.removeClass('mdc-text-field--invalid');
            this.$helper.removeClass('mdc-text-field-helper-text--persistent').html(this.helpTextShort);
        };
        this.onChange = function() {
            var value = this.getInputValue();
            var form = this.getForm();
            var $form = this.$form;
            if (this.isEmpty(value)) {
                this.$field.removeClass('drest-field--selected');
            } else {
                this.$field.addClass('drest-field--selected');
            }
            if (this.controls) {
                var show = this.controls[value || ''];
                $form.find('.drest-field')
                .each(function() {
                    var $field = $(this);
                    if ($field.hasClass('drest-field--fake')) {
                        return;
                    }
                    var name = $field.find('textarea, input, select')[0].name;
                    if (!show || show.length === 0) {
                        $field.removeClass('drest-hidden');
                    } else {
                        if (show.indexOf(name) > -1)  {
                            $field.removeClass('drest-hidden');
                        } else {
                            $field.addClass('drest-hidden');
                        }
                    }
                });
            }
            this.clearError();
            var was = field.value;
            this.value = value;
            if (this.hasChanged()) {
                this.$field.addClass('drest-field--changed');
            } else {
                this.$field.removeClass('drest-field--changed');
            }
            if (form) {
                form.$form.trigger('change', [{
                    field: this,
                    before: was,
                    after: value
                }]);
            }
        };

        var field = this;
        this._form = null;

        this.id = args.id;
        var $field = this.$field = $('#' + field.id);
        var $input = this.$input = $('#' + field.id + '-input');
        var $helper = this.$helper = $('#' + field.id + '-helper');
        var $form = this.$form = $field.closest('.drest-form');
        var $textField = this.$textField = $field.find('.mdc-text-field');
        var $select = this.$select = $field.find('.mdc-select');
        var $label = this.$label = field.$field.find('label, .drest-field__label');
        var relation = this.relation = args.relation;
        var value = this.initial = field.value = args.value;
        var label = this.label = args.label;
        var name = this.name = args.name;
        var type = this.type = args.type;
        var many = this.many = args.many || this.type === 'list';
        var required = this.required = args.required;
        var disabled = this.disabled = !$form.length || $form.hasClass('drest-form--readonly');

        this.controls = args.controls;
        this.readOnly = args.readOnly;
        this.helpTextShort = args.helpTextShort;
        this.helpText = args.helpText;
        this.writeOnly = args.writeOnly;

        var select2;

        //  set classes
        $field.addClass('drest-field--js');
        if (!this.isEmpty(value)) {
            $field.addClass('drest-field--selected');
        }

        // setup dependents and listeners
        if (type === 'list') {
            // fixed-style select2
            if (value) {
                for (var v in value) {
                    if (value.hasOwnProperty(v)) {
                        $input.append(
                            '<option value="' + value[v] + '" selected="selected">' + value[v] + '</option>'
                        );
                    }
                }
            }
            $input.select2({
                tags: true,
                placeholder: label,
                theme: 'material',
                minimumInputLength: 1,
                language: {
                    inputTooShort: function() {
                        return field.helpTextShort || "Start typing";
                    }
                },
                dropdownParent: $field
            });
            select2 = $input.data('select2');
        } else if (type === 'relation') {
            if (relation.image) {
                // images
                // many-type not yet supported
                this.value = this.initial = value.id;
            } else {
                // ajax-style select2
                var perPage = 25;
                var selected;
                var initials;
                var nameField = relation.nameField;
                var searchKey = relation.searchKey;
                var pkField = relation.pkField;
                var resourceName = relation.resourceName;
                var pluralName = relation.pluralName;
                var url = relation.url;

                var includes = [pkField];
                if (pkField !== nameField) {
                    includes.push(nameField);
                }
                var placeholder = many ? label : {
                    id: "",
                    placeholder: label
                };
                if (many) {
                    selected = [];
                    initials = [];
                    if (value) {
                        for (var i = 0; i<value.length; i++) {
                            var val = value[i];
                            initials.push({
                                id: val.id,
                                text: val.name,
                                name: val.name,
                                selected: true
                            });
                            selected.push(val.id);
                        }
                    }
                } else {
                    if (value && value.id) {
                        initials = [{
                            id: value.id,
                            text: value.name,
                            name: value.name,
                            selected: true
                        }];
                        selected = value.id;
                    } else {
                        initials = [];
                        selected = null;
                    }
                }
                $input.select2({
                    data: initials,
                    dropdownParent: $field,
                    language: {
                        inputTooShort: function() {
                            return field.helpTextShort;
                        }
                    },
                    width: 'resolve',
                    theme: 'material',
                    placeholder: placeholder,
                    allowClear: !required,
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
            // set selection
            $input.val(selected);

            select2 = $input.data('select2');
            // reset value from object form to canonical ID form
            // e.g. if the object form is {"id": "x", "name": "y", ...},
            // the canonical ID form is just "x"
            this.value = this.initial = selected;
          }

        } else if (type === 'boolean') {
            $input.off('click.drest-field').on('click.drest-field', function() {
                var $this = $(this);
                $this.attr('value', $this.is(':checked'));
            });
            if (value === null){
                $input[0].indeterminate = true;
                $input.attr('value', null);
            } else {
                $input.attr('value', $input.is(':checked'));
            }
        } else if (type === 'file') {
            $input.dropify();
            $input.on('dropify.afterClear', function(evt, el) {
                // clearing the dropify doesnt trigger input's change
                this.onChange();
            }.bind(this));
        }

        if (select2) {
            $field.off('click.drest-field').on('click.drest-field', function() {
                if (!$form.hasClass('drest-form--readonly')) {
                    $field.addClass('drest-field--focused');
                }
            });
            $input.on('select2:open', function(e){
                $field.addClass('drest-field--focused');
            });
            $input.on('select2:close', function(e){
                $field.removeClass('drest-field--focused');
                $field.removeClass('drest-field--invalid');
            });
            select2.on('results:message', function() {
                this.dropdown._resizeDropdown();
                this.dropdown._positionDropdown();
                this.$results.removeClass('has-results');
            });
            select2.on('results:all', function(data) {
                if (data.data.results && data.data.results.length) {
                    this.$results.addClass('has-results');
                } else {
                    this.$results.removeClass('has-results');
                }
            });
        }
        // bind change handler
        $input.off('change.drest-field').on('change.drest-field', this.onChange.bind(this));

        // trigger change
        if (field.controls || type === 'relation' || type === 'list') {
            $input.trigger('change');
        }

        // trigger disable
        if (this.disabled) {
            this.disable();
        }

        // set field
        $field[0].DRESTField = this;
    }

    var formId = 0;
    $('.drest-form').each(function() {
        var form = new DRESTForm($(this)[0]);
    });


    window.drest = {
        DRESTForm: DRESTForm,
        DRESTField: DRESTField,
        DRESTApp: DRESTApp
    };
});

// https://github.com/peledies/select2-tab-fix
// jQuery(document).ready(function(a){var b=a(document.body),c=!1,d=!1;b.on("keydown",function(a){var b=a.keyCode?a.keyCode:a.which;16==b&&(c=!0)}),b.on("keyup",function(a){var b=a.keyCode?a.keyCode:a.which;16==b&&(c=!1)}),b.on("mousedown",function(b){d=!1,1!=a(b.target).is('[class*="select2"]')&&(d=!0)}),b.on("select2:opening",function(b){d=!1,a(b.target).attr("data-s2open",1)}),b.on("select2:closing",function(b){a(b.target).removeAttr("data-s2open")}),b.on("select2:close",function(b){var e=a(b.target);e.removeAttr("data-s2open");var f=e.closest("form"),g=f.has("[data-s2open]").length;if(0==g&&0==d){var h=f.find(":input:enabled:not([readonly], input:hidden, button:hidden, textarea:hidden)").not(function(){return a(this).parent().is(":hidden")}),i=null;if(a.each(h,function(b){var d=a(this);if(d.attr("id")==e.attr("id"))return i=c?h.eq(b-1):h.eq(b+1),!1}),null!==i){var j=i.siblings(".select2").length>0;j?i.select2("open"):i.focus()}}}),b.on("focus",".select2",function(b){var c=a(this).siblings("select");0==c.is("[disabled]")&&0==c.is("[data-s2open]")&&a(this).has(".select2-selection--single").length>0&&(c.attr("data-s2open",1),c.select2("open"))})});

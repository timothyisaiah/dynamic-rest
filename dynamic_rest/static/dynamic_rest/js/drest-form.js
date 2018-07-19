/** dropify patches **/
$(function(){
    Dropify.prototype.isTouchDevice = function() { return false; }
    Dropify.prototype.getFileType = function() {
        return this.file.name.split('.').pop().split('?').shift().toLowerCase();
    };
    Dropify.prototype.cleanFilename = function(src) {
        var filename = src.split('\\').pop();
        if (filename == src) {
            filename = src.split('/').pop();
        }
        filename = filename.split('?')[0];
        return src !== "" ? filename : '';
    };
});

/** select2 patches **/

// https://github.com/peledies/select2-tab-fix
// jQuery(document).ready(function(a){var b=a(document.body),c=!1,d=!1;b.on("keydown",function(a){var b=a.keyCode?a.keyCode:a.which;16==b&&(c=!0)}),b.on("keyup",function(a){var b=a.keyCode?a.keyCode:a.which;16==b&&(c=!1)}),b.on("mousedown",function(b){d=!1,1!=a(b.target).is('[class*="select2"]')&&(d=!0)}),b.on("select2:opening",function(b){d=!1,a(b.target).attr("data-s2open",1)}),b.on("select2:closing",function(b){a(b.target).removeAttr("data-s2open")}),b.on("select2:close",function(b){var e=a(b.target);e.removeAttr("data-s2open");var f=e.closest("form"),g=f.has("[data-s2open]").length;if(0==g&&0==d){var h=f.find(":input:enabled:not([readonly], input:hidden, button:hidden, textarea:hidden)").not(function(){return a(this).parent().is(":hidden")}),i=null;if(a.each(h,function(b){var d=a(this);if(d.attr("id")==e.attr("id"))return i=c?h.eq(b-1):h.eq(b+1),!1}),null!==i){var j=i.siblings(".select2").length>0;j?i.select2("open"):i.focus()}}}),b.on("focus",".select2",function(b){var c=a(this).siblings("select");0==c.is("[disabled]")&&0==c.is("[data-s2open]")&&a(this).has(".select2-selection--single").length>0&&(c.attr("data-s2open",1),c.select2("open"))})});

function DRESTApp(config) {
    this.slideTo = function($slide) {
        if (this.submitting) {
            // ignore during submit
            return;
        }
        if (!$slide.hasClass('swiper-slide')) {
            $slide = $slide.closest('.swiper-slide');
        }
        if (!$slide.length) {
            throw 'invalid slideTo argument';
        }
        var currentIndex = this.currentIndex;
        if (currentIndex === 0) {
            // for main form, save the scroll position on scroll back
            var scrollTop = $('html, body').scrollTop();
            $(this.currentSlide).attr('data-scroll-top', scrollTop);
        }
        var newIndex = $slide.index();
        var toEditMode = newIndex > 0;
        var $slides = this.$slides;
        for (var i=0; i<$slides.length; i++) {
            var $slide = $($slides[i]);
            if (i !== newIndex && i !== currentIndex) {
                $slide.hide();
            } else {
                $slide.show();
            }
        }
        this.currentIndex = newIndex;
        this.currentSlide = this.$slides[this.currentIndex];

        this.swiper.update();
        this.swiper.slideTo(newIndex);

        var $form = $(this.currentSlide).find('.drest-form');
        this.currentForm = $form.length ? $form[0].DRESTForm : null;

        this.clearError();
        this.clearChanged();

        if (toEditMode) {
            // set edit styles
            this.enableEdit();
        } else {
            // remove edit styles
            this.disableEdit();
        }
    };
    this.doDelete = function() {
        this.setSubmitting();
        $.ajax({
            url: this.detailEndpoint,
            method: 'DELETE',
            dataType: 'json',
            headers: {
              'Accept': 'application/json'
            }
        }).done(this.onDeleteOk.bind(this))
        .fail(this.onDeleteFailed.bind(this))
    };
    this.getTime = function() {
        return Math.round((new Date()).getTime());
    };
    this.onScroll = function() {
        this.setScrolling();

        var scrollHideTime = 1000 * this.scrollHideSeconds;
        this.scrollEndTime = this.getTime() + scrollHideTime;
        if (!this._scrollTimeout) {
            this._scrollTimeout = setTimeout(
                this.scrollCancel.bind(this),
                scrollHideTime
            );
        }
    };
    this.scrollCancel = function() {
        var time = this.getTime();
        var diff = this.scrollEndTime - time;
        if (diff <= 0) {
            this.clearScrolling();

            delete this.scrollEndTime;
            delete this._scrollTimeout;
        } else {
            this._scrollTimeout = setTimeout(
                this.scrollCancel.bind(this),
                diff
            );
        }
    };
    this.onDeleteFailed = function() {
        this.clearSubmitting();
        this.setError();
    };
    this.onDeleteOk = function() {
        this.showNotice('Deleted successfully, redirecting...');
        window.location = this.listEndpoint;
    };
    this.confirmDelete = function() {
        this.showDialog({
            title: 'You are about to delete a record!',
            body: 'Are you sure? This operation cannot be undone!',
            onAccept: this.doDelete.bind(this)
        });
    };
    this.showNotice = function(opts) {
        if (typeof opts === 'string') {
            opts = {
                message: opts
            }
        }
        opts = opts || {};
        var notice = this.notice;
        notice.show(opts);
    };
    this.showDialog = function(opts) {
        opts = opts || {};
        var title = opts.title;
        var body = opts.body;
        var onAccept = opts.onAccept;
        var showAccept = !!onAccept;
        var showCancel = true;
        var acceptLabel = opts.acceptLabel || 'Ok';
        var cancelLabel = opts.cancelLabel || 'Cancel';

        var dialog = this.dialog;
        var $dialog = this.$dialog;
        var $acceptLabel = $dialog.find('.drest-dialog__accept');
        var $cancelLabel = $dialog.find('.drest-dialog__cancel');
        var $title = $dialog.find('.drest-dialog__title');
        var $body = $dialog.find('.drest-dialog__body');

        if (!showAccept) {
            $acceptLabel.hide().off('click.drest');
        } else {
            $acceptLabel.html(acceptLabel).show().off('click.drest');
            $acceptLabel.on('click.drest', function() {
                if (onAccept) {
                    onAccept();
                }
                dialog.close();
            });
        }
        if (!showCancel) {
            $cancelLabel.hide().off('click.drest');
        } else {
            $cancelLabel.html(cancelLabel).show().off('click.drest').on('click.drest', function() {
                dialog.close();
            });
        }
        $title.html(title);
        $body.html(body);

        dialog.show();
    };
    this.enableEdit = function() {
        var form = this.currentForm;
        this.$title.html(form.getTitle());
        form.enable();
        this.setEditing();
    };
    this.disableEdit = function() {
        var form = this.currentForm;
        this.$title.html(this.originalTitle);
        if (form && form.type === 'edit') {
            form.disable();
        }
        this.clearEditing();
    };
    this.setEditing = function() {
        this.editing = true;
        this.$header.addClass('drest-app--editing');
        this.$fab.addClass('drest-app--editing');
    };
    this.clearEditing = function() {
        this.editing = false;
        this.$header.removeClass('drest-app--editing');
        this.$fab.removeClass('drest-app--editing');
    }
    this.setScrolling = function() {
        this.scrolling = true;
        this.$.addClass('drest-app--scrolling');
        this.$header.addClass('drest-app--scrolling');
    };
    this.clearScrolling = function() {
        this.scrolling = false;
        this.$.removeClass('drest-app--scrolling');
        this.$header.removeClass('drest-app--scrolling');
    };
    this.setError = function() {
        this.error = true;
        this.$.addClass('drest-app--error');
        this.$header.addClass('drest-app--error');
    };
    this.clearError = function() {
        this.error = false;
        this.$.removeClass('drest-app--error');
        this.$header.removeClass('drest-app--error');
    };
    this.clearSubmitting = function() {
        this.submitting = false;
        this.$header.removeClass('drest-app--submitting');
    };
    this.setSubmitting = function() {
        this.submitting = true;
        this.$header.addClass('drest-app--submitting');
    };
    this.setChanged = function() {
        this.changed = true;
        this.$header.addClass('drest-app--changed');
    };
    this.clearChanged = function() {
        this.changed = false;
        this.$header.removeClass('drest-app--changed');
    };
    this.onEditFailed = function() {
        this.clearSubmitting();
        this.setError();
        this.focusError();
        this.showNotice('An error occurred');
    };
    this.focusError = function() {
        var $error = this.currentForm.$.find('.drest-field--invalid').first();
        if ($error.length) {
            $('body, html').animate({
                scrollTop: $error.offset().top - $(window).height() / 2
            }, 200);
            $error.find('input').focus();
        }
    };
    this.onEditNoop = function() {
        this.clearSubmitting();
        this.disableEdit();
    };
    this.onEditOk = function() {
        this.clearSubmitting();
        this.clearChanged();
        this.disableEdit();
        this.showNotice('Saved successfully');
    };
    this.onAddFailed = function() {
        this.clearSubmitting();
        this.setError();
        this.focusError();
        this.showNotice('An error occurred');
    };
    this.onAddOk = function(e, response) {
        var url = response.data.links.self;
        this.clearError();
        this.clearChanged();

        this.showNotice('Saved successfully, redirecting...');
        window.location = url;
    };
    this.save = function() {
        if (this.submitting || !this.currentForm) {
            return;
        }
        // save primary record
        this.setSubmitting();
        this.currentForm.submit();
    };
    this.back = function(e) {
        var form = this.currentForm;
        var app = this;
        if (this.submitting || !form) {
            return;
        }

        // prevent click on section
        e.preventDefault();
        e.stopPropagation();

        var onAccept = function() {
            form.reset();
            app.clearError();
            app.clearChanged();

            if (form === app.editForm) {
                app.disableEdit();
            } else {
                app.slideTo(app.$mainSlide);
            }
        };

        if (form.hasChanged()) {
            this.showDialog({
                title: 'You have unsaved changed!',
                body: 'Are you sure you want to go back and discard them?',
                onAccept: onAccept
            });
        } else {
            onAccept();
        }
    };
    this.resetHeight = function() {
        this.$.find('.swiper-wrapper')
            .css('height', $(this.currentSlide).outerHeight());
    };
    this.getForms = function() {
        var $forms = this.$.find('.drest-form');
        var forms = [];
        for (var i=0; i<$forms.length; i++) {
            forms.push($forms[i].DRESTForm);
        }
        return forms;
    };
    this.getEditForm = function() {
        if (this.style === 'detail') {
            var form = this.$.find('.drest-form--edit')[0];
            return form.DRESTForm;
        }
        return null;
    };
    this.getAddForm = function() {
        if (this.style === 'list') {
            var form = this.$.find('.drest-form--add');
            return form.length ? form[0].DRESTForm : null;
        }
        return null;
    };
    this.onFormChange = function(e, data) {
        var form = data.form;
        if (form === this.currentForm) {
            if (form.hasChanged()) {
                this.setChanged();
            } else {
                this.clearChanged();
            }
            if (form.hasError()) {
                this.setError();
            } else {
                this.clearError();
            }
        }
    };
    this.onLoad = function() {
        var app = this;
        var config = this.config;
        var $header = this.$header = $(config.header);
        this.$ = $(config.content);
        this.scrollHideSeconds = config.scrollHideSeconds || 2;
        this.$.show();
        this.$table = $(config.table);
        this.$fab = $(config.fab);
        this.$drawer = $(config.drawer);
        this.$drawerHeader = this.$drawer.find('.drest-drawer__header');
        this.style = config.style; // either list, directory, detail, or error
        this.detailEndpoint = config.detailEndpoint;
        this.listEndpoint = config.listEndpoint;
        this.$cancelButton = $header.find('.drest-app__cancel-button');
        this.$moreButton = $header.find('.drest-app__more-button');
        this.$filterButton = $header.find('.drest-app__filter-button');
        this.$saveButton = $header.find('.drest-app__save-button');
        this.$deleteButton = $header.find('.drest-app__delete-button');
        this.$spinner = $header.find('drest-app__spinner');
        this.$navSection = $header.find('.drest-app__navigation');
        this.$backButton = $header.find('.drest-app__back-button');
        this.$title = $header.find('.drest-app__title');
        this.$moreMenu = $header.find('.drest-app__more-menu');
        this.$swiper = $(config.content + ' .swiper-container');
        this.originalTitle = this.$title.html();
        this.dialog = new mdc.dialog.MDCDialog(document.querySelector(config.dialog));
        this.$dialog = $(config.dialog);

        this.notice = new mdc.snackbar.MDCSnackbar(document.querySelector(config.notice));
        this.$notice = $(config.notice);

        if (this.$deleteButton.length) {
            this.$deleteButton.off('click.drest').on('click.drest', this.confirmDelete.bind(this));
        }
        this.$.find('.drest-grid').each(function() {
            var items = $(this).find('> .drest-grid__item').length;
            if (items === 1) {
                $(this).addClass('drest-grid--1x');
            } else if (items === 2) {
                $(this).addClass('drest-grid--2x');
            }
        });
        if (this.$table.length) {
            this.$table.DataTable({
                "paging": false,
                "ordering": false,
                "info": false,
                "searching": false,
                "fixedHeader": true,
                "responsive": {
                    "details": false
                },
            });
        }
        if (this.$drawer.length) {
            this.drawer = new mdc.drawer.MDCTemporaryDrawer(this.$drawer[0]);
            if (this.$drawerHeader.length) {
                this.$drawerHeader.on('click', function() {
                    this.drawer.open = false;
                }.bind(this));
            }
        }
        if (this.$moreMenu.length) {
            this.moreMenu = new mdc.menu.MDCMenu(this.$moreMenu[0]);
            this.$moreButton.on('click.drest', function() {
                this.moreMenu.open = !this.moreMenu.open;
            }.bind(this));
        }
        this.$navSection.on('click', function() {
            if (this.editing || this.submitting) {
                return;
            } else {
                this.drawer.open = true;
            }
        }.bind(this));
        if (this.$swiper.length) {
            this.swiper = new Swiper(config.content + ' .swiper-container', {
                noSwipingSelector: '*',
                speed: 10,
                autoHeight: true,
                on: {
                    transitionEnd: function() {
                        var $slide = $(app.currentSlide);
                        var scrollTop = $slide.attr('data-scroll-top') || 0;
                        $('body, html').scrollTop(scrollTop);
                        app.resetHeight();
                    }
                }
            });
            this.$slides = this.$swiper.find('.swiper-slide');
            this.currentIndex = 0;
            this.currentSlide = this.$slides[0];
            this.$mainSlide = $(this.currentSlide);
            var $form = this.$mainSlide.find('.drest-form');
            this.currentForm = $form.length ? $form[0].DRESTForm : null;
            this.$addSlide = this.$swiper.find('.drest-form--add').closest('.swiper-slide');
            this.$filterSlide = this.$swiper.find('.drest-form--filter').closest('.swiper-slide');
        }
        this.forms = this.getForms();
        for (var i=0; i<this.forms.length; i++) {
            var form = this.forms[i];
            form.$.on('drest-form:change', this.onFormChange.bind(this));
        }
        if (this.style === 'detail') {
            this.editForm = this.getEditForm();
            this.editForm.$.on('drest-form:submit-succeeded', this.onEditOk.bind(this));
            this.editForm.$.on('drest-form:submit-failed', this.onEditFailed.bind(this));
            this.editForm.$.on('drest-form:submit-noop', this.onEditNoop.bind(this));
            this.$fab.on('click.drest', this.enableEdit.bind(this));
            this.$.find('.drest-form--add-related')
                .on('drest-form:submit-succeeded', this.onAddOk.bind(this))
                .on('drest-form:submit-failed', this.onAddFailed.bind(this));
        } else if (this.style === 'list') {
            this.addForm = this.getAddForm();
            this.$.find('.drest-form--add')
                .on('drest-form:submit-succeeded', this.onAddOk.bind(this))
                .on('drest-form:submit-failed', this.onAddFailed.bind(this));
        }
        $('.drest-app__slide-to').each(function() {
            var $button = $(this);
            var target = $button.attr('data-target');
            $button.on('click.drest', function() {
                app.slideTo($(target))
            });
        });
        if (this.$saveButton.length) {
            this.$saveButton.on('click.drest', this.save.bind(this));
        }
        if (this.$backButton.length) {
            this.$backButton.on('click.drest', this.back.bind(this));
        }
        $(window).scroll(this.onScroll.bind(this));
        this.resetHeight();
    };

    this.editing = false;
    this.submitting = false;
    this.config = config;

    $(this.onLoad.bind(this));
}

function DRESTForm(config) {
    this.submit = function() {
        return this.$.submit();
    };
    this.getFields = function() {
        if (typeof this._fields === 'undefined') {
            var fields = this.$fields.map(function() {
                return this.DRESTField;
            });
            this._fields = fields;
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
        if (typeof this._fieldsByName === 'undefined') {
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
            this.enable();
        } else {
            this.disable();
        }
    };
    this.enable = function() {
        if (!this.disabled) {
            return;
        }
        this.$.removeClass('drest-form--readonly');
        this.getFields().each(function() {
            if (!this.readOnly) {
                this.enable();
            }
        });
        this.disabled = false;
    };
    this.disable = function() {
        if (this.disabled) {
            return;
        }
        this.$.addClass('drest-form--readonly');
        this.getFields().each(function() {
            this.disable();
        });
        this.disabled = true;
    };
    this.getTitle = function() {
        var verb;
        var icon;
        if (this.type === 'add') {
            verb = 'Adding';
            icon = 'plus';
        } else if (this.type === 'add-related') {
            verb = 'Adding';
            icon = 'plus';
        } else if (this.type === 'filter') {
            verb = 'Finding';
            icon = 'search';
        } else if (this.type === 'edit') {
            verb = 'Editing';
            icon = 'pencil';
        }
        return '<span class="mdi mdi-' + icon + '"/>  ' + verb + ' ' + this.resourceName;
    };
    this.reset = function() {
        this.getFields().each(function() {
            if (this.hasChanged()) {
                this.reset(this.initial);
            } else {
                this.clearError();
            }
        });
    };
    this.hasError = function() {
        var fields = this.getFields();
        for (var i=0; i<fields.length; i++) {
            var field = fields[i];
            if (field.hasError) {
                return true;
            }
        }
        return false;
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
        var form = this.$;
        var method = (form.data('method') || form.attr('method') || 'GET').toUpperCase();

        if (method === 'GET') {
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
                if (method !== 'PATCH' || f.hasChanged()) {
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
        console.log(errors);
        var fields = this.getFieldsByName();
        var hasFieldErrors = false;
        for (var key in fields) {
          if (fields.hasOwnProperty(key)) {
            var error = errors[key];
            var f = fields[key];
            if (error) {
                hasFieldErrors = true;
                f.setError(error[0]);
            } else {
                f.clearError(true);
            }
          }
        }
        if (!hasFieldErrors) {
            window.app.showDialog({
                title: 'Failed to save!',
                body: errors.error || errors,
            });
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
                field.clearError(true);
            }
        }
    };

    this.onLoad = function() {
        this.$ = $(this.config.container);
        this.$.addClass('drest-form--js');
        this.$fields = this.$.find('.drest-field').not('.drest-field--fake');
        this.fields = this.getFields();
        this.disabled = this.$.hasClass('drest-form--readonly');
        this.$.on('drest-form:submit-failed', this.onSubmitFailed.bind(this));
        this.$.on('drest-form:submit-succeeded', this.onSubmitSucceeded.bind(this));
        this.$.off('submit.drest-form').on('submit.drest-form', this.onSubmit.bind(this));
        this.$.trigger('drest-form:loaded');
    }

    this.config = config;
    this.type = config.type;
    this.resourceName = config.resourceName;
    var container = document.querySelector(this.config.container);
    container.DRESTForm = this;
    $(this.onLoad.bind(this));
}

function DRESTField(config) {
    this.getSubmitValue = function() {
        if (this.type === 'file') {
            var input = this.$input[0];
            var files = input.files;
            return (files && files.length) ? files[0] : null;
        } else if (this.type !== 'text' && this.value === '') {
            return null;
        }
        return this.value;
    };
    this.getInputValue = function() {
        var val = this.$input.val();
        if (val === '' && this.type !== 'text') {
            val = null;
        }
        if (val === null && this.many &&
            (this.type === 'relation' || (this.initial && this.initial.length === 0))
        ) {
            // replace null with empty list for
            // a many relation, or if the initial value was an empty list
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
    this.getTextField = function() {
        if (typeof this._textField === 'undefined') {
            var el = this.$textField.length ? this.$textField[0] : null;
            if (el && el.MDCTextField) {
                this._textField = el.MDCTextField;
            } else {
                this._textField = null;
            }
        }
        return this._textField;
    };
    this.getForm = function() {
        if (typeof this._form === 'undefined') {
            var el = this.$form[0];
            if (el.DRESTForm) {
                this._form = el.DRESTForm;
            }
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
        if (value === '' && this.type !== 'text') {
            value = null;
        }
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
                if (value && value.length) {
                    for (var i=0; i<value.length; i++) {
                        var v = value[i];

                        if (!this.$input.find('option[value="' + v + '"]').length) {
                            this.$input.append(
                                '<option value="' + v + '">' + v + '</option>'
                            );
                        }
                    }
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
        this.clearError(true);
        if (this.type === 'relation' || this.type === 'list') {
            this.addSelect2ChoiceHandlers();
        }
    };
    this.setError = function(error) {
        this.error = error;
        this.hasError = true;
        // this is sticky through change until submit
        this.valueOnError = this.getInputValue();
        this.$field.addClass('drest-field--invalid');
        var textField = this.getTextField();
        if (textField) {
            textField.valid = false;
        }
        this.$select.addClass('mdc-text-field--invalid');
        this.$helper
            .addClass('mdc-text-field-helper-text--persistent')
            .addClass('mdc-text-field-helper-text--validation-msg')
            .html(error);
    };
    this.clearError = function(permanent) {
        if (permanent) {
            this.error = null;
            this.valueOnError = undefined;
        }

        this.hasError = false;
        this.$field.removeClass('drest-field--invalid');
        this.$select.removeClass('mdc-text-field--invalid');
        var textField = this.getTextField();
        if (textField) {
            textField.valid = true;
        }
        this.$helper
            .removeClass('mdc-text-field-helper-text--persistent')
            .removeClass('mdc-text-field-helper-text--validation-msg')
            .html(this.helpTextShort);
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
            // TODO: make this good
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
            if (window.app) {
                window.app.resetHeight();
            }
        }
        var was = this.value;
        this.value = value;

        if (this.error) {
            // set or temp-clear error
            if (this.equal(this.value, this.valueOnError)) {
                this.setError(this.error);
            } else {
                this.clearError();
            }
        }
        if (this.hasChanged()) {
            this.$field.addClass('drest-field--changed');
        } else {
            this.$field.removeClass('drest-field--changed');
        }
        if (form) {
            form.$.trigger('drest-form:change', [{
                field: this,
                form: form,
                before: was,
                after: value
            }]);
        }
    };

    this.onLoad = function() {
        var config = this.config;
        var field = this;
        this.id = config.id;
        var $field = this.$ = this.$field = $('#' + field.id);
        var $input = this.$input = $('#' + field.id + '-input');
        if ($input.is('textarea') && autosize) {
            autosize($input[0]);
        }
        var $helper = this.$helper = $('#' + field.id + '-helper');
        var $form = this.$form = $field.closest('.drest-form');
        var $textField = this.$textField = $field.find('.mdc-text-field');
        var $select = this.$select = $field.find('.mdc-select');
        var $label = this.$label = field.$field.find('label, .drest-field__label');
        var type = this.type = config.type;
        var relation = this.relation = config.relation;

        var value = config.value;
        if (value === '' && this.type !== 'text') {
            value = null;
        }

        this.initial = this.value = value;
        var label = this.label = config.label;
        var name = this.name = config.name;
        var many = this.many = config.many || this.type === 'list';
        var required = this.required = config.required;
        var disabled = this.disabled = !$form.length || $form.hasClass('drest-form--readonly');

        this.controls = config.controls;
        this.readOnly = config.readOnly;
        this.helpTextShort = config.helpTextShort;
        this.helpText = config.helpText;
        this.writeOnly = config.writeOnly;

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
        } else if (type === 'datetime' || type === 'date' || type === 'time') {
            var inputType = type;
            var opts = { clearButton: true };

            if (inputType == 'time') {
                opts.date = false;
                $input.bootstrapMaterialDatePicker(opts);
            } else if (inputType == 'date') {
                opts.time = false;
                opts.format = 'YYYY-MM-DD';
                $input.bootstrapMaterialDatePicker(opts);
            } else if (inputType == 'datetime' || inputType == 'datetime-local') {
                opts.format = 'YYYY-MM-DD hh:mm';
                $input.bootstrapMaterialDatePicker(opts);
            }
            $input.on('open', function(e) {
                if ($field.hasClass('drest-field--disabled')) {
                    e.stopPropagation();
                    return false;
                }
                $field.addClass('drest-field--focused');
                $field.find('.mdc-line-ripple').addClass('mdc-line-ripple--active');
            });
            $input.on('close', function() {
                $field.removeClass('drest-field--focused');
                $field.find('.mdc-line-ripple').removeClass('mdc-line-ripple--active');
            });
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
            $input.dropify({
                tpl: {
                    clearButton: '<span class="material-icons small drest-field__clear">cancel</span>'
                }
            });
            $input.on('dropify.afterClear', function(evt, el) {
                // clearing the dropify doesnt trigger input's change
                this.onChange();
            }.bind(this));
            $field.find('.dropify-preview')
            .addClass('drest--clickable')
            .off('click.drest').on('click.drest', function() {
                if (this.disabled && this.value) {
                    window.open(this.value, '_blank');
                }
            }.bind(this));
        }

        if (select2) {
            // change styles
            $field.find(".select2-selection__arrow")
            .addClass("material-icons")
            .html("arrow_drop_down");

            // open select2 whenever the field is clicked in edit mode
            $field.off('click.drest-field').on('click.drest-field', function() {
                if (!this.disabled && !$form.hasClass('drest-form--readonly')) {
                    $input.select2('open');
                }
            }.bind(this));
            // add focused class whenever the select2 is open
            $input.on('select2:open', function(e){
                $field.addClass('drest-field--focused');
            });
            $input.on('select2:close', function(e){
                $field.removeClass('drest-field--focused');
            });
            // fix dropdown positioning
            select2.on('results:message', function() {
                this.dropdown._resizeDropdown();
                this.dropdown._positionDropdown();
                this.$results.removeClass('has-results');
            });
            // set has-results on select2-results for styling
            // empty results differently
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
    };

    this.config = config;
    var container = document.querySelector('#' + this.config.id);
    container.DRESTField = this;
    $(this.onLoad.bind(this));
}

window.drest = {
    DRESTApp: DRESTApp,
    DRESTForm: DRESTForm,
    DRESTField: DRESTField
};

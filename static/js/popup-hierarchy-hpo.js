;(function ($) {

	var CSS_PREFIX = 'popup-hierarchy-hpo-';

	var DEFAULT_SETTINGS = {
		// Search settings
		method: "GET",
		queryParam: "q",
		searchDelay: 300,
		jsonContainer: null,
		contentType: "json",

		nodeName: 'div',

		cssInlineContentClass: CSS_PREFIX+'inline-content',
		cssTableClass: CSS_PREFIX+'table',
		cssTrClass: CSS_PREFIX+'tr',
		cssTdClass: CSS_PREFIX+'td',

		cssBaseClass: CSS_PREFIX+'base',
		cssTitleClass: CSS_PREFIX+'title',
		cssContentClass: CSS_PREFIX+'content',
		cssLinkBaseClass: CSS_PREFIX+'link-base',
		cssLinkClass: CSS_PREFIX+'link',
		cssLinkFocusClass: CSS_PREFIX+'link-focus',

		cssSelfContentClass: CSS_PREFIX+'self-content',
		cssOtherContentClass: CSS_PREFIX+'other-content',
		cssCloseButtonClass: CSS_PREFIX+'close-button',

		cssSelectedPhenotypeClass: CSS_PREFIX+'selectedphenotype',

		cssButtonBaseClass: CSS_PREFIX+'buttons-base',
		cssButtonsClass: CSS_PREFIX+'buttons',
		cssContentTableClass: CSS_PREFIX+'content-table',
		cssContentTrClass: CSS_PREFIX+'content-tr',
		cssContentThClass: CSS_PREFIX+'content-th',
		cssContentTdClass: CSS_PREFIX+'content-td',

		cssLoadingClass: CSS_PREFIX+'loading',
		loadingText: 'Loading...',

		titleSuperclass : 'superclass',
		titleSubclass : 'subclass',
		titleSelfclass : 'selfclass',

		keySuperclass : 'superclass',
		keySubclass : 'subclass',
		keySelfclass : 'selfclass',

		language : {
			'ja' : {
				superclass : '上位',
				subclass : '下位',
				selectedphenotype: '選択した症状',
				replace : '置換',
				add : '追加',
				jpn : 'JPN',
				eng : 'ENG',
				revert : '元に戻す'
			},
			'en' : {
				superclass : 'superclass',
				subclass : 'subclass',
				selectedphenotype: 'selected phenotype',
				replace : 'Replace',
				add : 'Add',
				jpn : 'JPN',
				eng : 'ENG',
				revert : 'revert'
			}
		}
	};

	var TOKENINPUT_SETTINGS_KEY = 'settings';

	var KEY_PREFIX = 'popupRelationHPO',
	SETTINGS_KEY = KEY_PREFIX+'Settings',
	OBJECT_KEY = KEY_PREFIX+'Object';

	var isObject = function(value) {
		return $.isPlainObject(value);
	},
	isArray = function(value) {
		return $.isArray(value);
	},
	isFunction = function(value) {
		return $.isFunction(value);
	},
	isNumeric = function(value) {
		return $.isNumeric(value);
	},
	isString = function(value) {
		return typeof value === 'string';
	},
	isBoolean = function(value) {
		return typeof value === 'boolean';
	},
	hasJA = function( str ) {
		return ( str.match(/[\u30a0-\u30ff\u3040-\u309f\u3005-\u3006\u30e0-\u9fcf]+/) )? true : false
	};

	var methods = {
		init: function(url_or_data_or_function, options) {
			var settings = $.extend({}, DEFAULT_SETTINGS, options || {});
			return this.each(function () {
				$(this).data(SETTINGS_KEY, settings);
				PopupRelationHPO(this, url_or_data_or_function, settings);
			});
		},
	};

	$.fn.popupRelationHPO = function (method) {
		if (methods[method]) {
			return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
		} else {
			return methods.init.apply(this, arguments);
		}
	};


	var PopupRelationHPO = function (input, url_or_data, settings) {

		var cache = new $.TokenList.Cache();

		function computeURL() {
			var current_settings = $(input).data(SETTINGS_KEY);
			return isFunction(current_settings.url) ? settings.url.call(current_settings) : current_settings.url;
		}

		function getTokenInputItems(){
			return $(input).tokenInput('get');
		}
		function addTokenInputItem(token){
			return $(input).tokenInput('add',token);
		}
		function clearTokenInputItems(){
			return $(input).tokenInput('clear');
		}

		function existsTokenInputItemFromID(hpo_id){
			var tokenInputItems = getTokenInputItems();
			var target_arr = [];
			if($.isArray(tokenInputItems)){
				target_arr = $.grep(tokenInputItems,function(data){return data.id===hpo_id;});
			}
			return target_arr.length!==0;
		}

		function getTokenInputItemFromName(hpo_name){
			var tokenInputItems = getTokenInputItems();
			var target_arr = [];
			if($.isArray(tokenInputItems)){
				target_arr = $.grep(tokenInputItems,function(data){return data.name===hpo_name;});
			}
			return target_arr.length>0 ? target_arr[0] : null;
		}

		function createOtherContent(values,options) {
			options = options || {};
			var current_settings = $(input).data(SETTINGS_KEY);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).addClass(current_settings.cssOtherContentClass); //.appendTo($tr);
			if($.isArray(values) && values.length){
				var $base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssOtherContentClass).appendTo($td);
				if(isString(options.classname)) $base.addClass(options.classname);
				if(isString(options['title']) && options['title'].length){
					var $title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTitleClass).text(options['title']).appendTo($base);
				}
				var $content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).appendTo($base);

				var add_css = {
					'display':'table-cell',
					'vertical-align':'top',
					'width':'32px'
				};
				$.each(values.sort(function(a,b){
					var a_name = a.name;
					var b_name = b.name;
					if(runSearchOptions.hasJA && isString(a.name_ja)) a_name = a.name_ja;
					if(runSearchOptions.hasJA && isString(b.name_ja)) b_name = b.name_ja;
					return a_name<b_name?-1:(a_name>b_name?1:0)
				}), function(){
					var text = this.name;
					if(runSearchOptions.hasJA && isString(this.name_ja)) text = this.name_ja;

					if(isNumeric(this.count)){
						text += ' ('+this.count+')';
					}

					var data = {
						'target' : $.extend({},tokeninput_target),
						'self' : $.extend({},this)
					};

					var $link_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLinkBaseClass).appendTo($content);
					if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySubclass){
						addExecuteButtons(data, existsTokenInputItemFromID(this.id)).appendTo($link_base).css(add_css);
					}

					$('<a>')
					.addClass(current_settings.cssLinkClass)
					.text(text)
					.attr({'href':'#'})
					.data(OBJECT_KEY, this)
					.click(function(){
						var data = $(this).data(OBJECT_KEY);

						if(false){
							if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySubclass){
								$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-subclass-translate 500ms ease-out 0s normal both'});
							}
							else if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySuperclass){
								$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-superclass-translate 500ms ease-out 0s normal both'});
							}
							setTimeout(function(){
								runSearch(data.id);
							},500);
						}else{
							setTimeout(function(){
								runSearch(data.id);
							},0);
						}
						return false;
					})
					.appendTo($link_base);

					if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySuperclass){
						addExecuteButtons(data, existsTokenInputItemFromID(this.id)).appendTo($link_base).css(add_css);
					}

				});
			}
			return $td;
		}

		function executionAddOrReplace(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};

			var new_token = {id: params.self.id, name: params.self.id+' '+params.self.name};
			if(runSearchOptions.hasJA && isString(params.self.name_ja)) new_token['name'] = params.self.id+' '+params.self.name_ja;

			if(params.exec==='add'){
				addTokenInputItem(new_token);
				$button.parent(current_settings.nodeName+'.'+current_settings.cssButtonBaseClass).find('button').off('click',executionAddOrReplace).css({opacity:0.2,cursor:'default'});
			}
			else if(params.exec==='replace'){
				var new_arr = [];
				var arr = getTokenInputItems();
				if($.isArray(arr)){
					$.each(arr, function(){
						if(this.id===params.target.id){
							new_arr.push(new_token);
						}
						else{
							new_arr.push(this);
						}
					});
				}
				if(new_arr.length){
					clearTokenInputItems();
					$.each(new_arr, function(){
						addTokenInputItem(this);
					});
				}
				closeMagnificPopup();
			}
		}

		function addExecuteButtons(data,disabled){
			if(!isBoolean(disabled)) disabled = disabled ? true : false;

			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);

			$.each(['add','replace'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-primary').data(OBJECT_KEY,  $.extend({},data,{'exec' : key.toLowerCase()})   ).text(settings.language[getCurrentLanguage()][key]).appendTo($button_base);
				if(!disabled){
					$button.on('click',executionAddOrReplace);
				}else{
					$button.css({opacity:0.2,cursor:'default'});
				}
			});
			return $button_base;
		}

		function executionLanguage(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};
			runSearchOptions.hasJA = params.exec==='jpn';
			setTimeout(function(){
				showResults();
			},100);
		}

		function addLanguageButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			$.each(['jpn','eng'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-success').data(OBJECT_KEY,  $.extend({},{'exec' : key.toLowerCase()})   ).text(settings.language[getCurrentLanguage()][key]).appendTo($button_base);
				$button.on('click',executionLanguage);
			});
			return $button_base;
		}

		function executionRevert(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};
			var hasJA = params.exec==='jpn';
			setTimeout(function(){
				showResults(tokeninput_target_results);
			},100);
		}

		function addRevertButton(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			$.each(['revert'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-primary').data(OBJECT_KEY,  $.extend({},{'exec' : key.toLowerCase()})   ).text(settings.language[getCurrentLanguage()][key]).appendTo($button_base);
				$button.on('click',executionRevert);
			});
			return $button_base;
		}

		function getInlineContent(){
			var cssInlineContentElement = current_settings.nodeName+'.'+current_settings.cssInlineContentClass;
			var $inlineContent = $(cssInlineContentElement);
			if($inlineContent.length==0){
				$inlineContent = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssInlineContentClass).appendTo($(document.body));
			}
			return $inlineContent;
		}
		function emptyInlineContent(){
			var $inlineContent = getInlineContent();
			return $inlineContent.empty();
		}

		function getCurrentLanguage(){
			return runSearchOptions.hasJA ? 'ja' : 'en';
		}

		var __last_results = null;
		function showResults(results) {
			if(results){
				__last_results = $.extend({},results);
			}else if(__last_results){
				results = $.extend({},__last_results);
			}
			if(!results){
				emptyInlineContent();
				return;
			}

			var current_settings = $(input).data(SETTINGS_KEY);

			if(!tokeninput_target){
				tokeninput_target_results = $.extend({},results);
				tokeninput_target = $.extend({},results[current_settings.keySelfclass][0]);
			}

			var $inlineContent = emptyInlineContent();
			var $table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).appendTo($inlineContent);

			//selected phenotype
			var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
			var $selectedphenotype_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssSelectedPhenotypeClass).appendTo($td);
			var $selectedphenotype_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTitleClass).appendTo($selectedphenotype_base);
			$selectedphenotype_title.empty();
			var $selectedphenotype_title_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','empty-cells':'hide','width':'100%'}).appendTo($selectedphenotype_title);
			var $selectedphenotype_title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($selectedphenotype_title_table);
			var $selectedphenotype_title_td_left = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'4px'}).text(settings.language[getCurrentLanguage()]['selectedphenotype']).appendTo($selectedphenotype_title_tr);
			var $selectedphenotype_title_td_center = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'center','width':'100px'}).appendTo($selectedphenotype_title_tr);
			addLanguageButtons().appendTo($selectedphenotype_title_td_center);
			var $selectedphenotype_title_td_right = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','width':'20px','padding-left':'4px'}).appendTo($selectedphenotype_title_tr);
			addRevertButton().appendTo($selectedphenotype_title_td_right);

			var selectedphenotype_content_text = tokeninput_target.id+' ';
			if(runSearchOptions.hasJA && tokeninput_target.name_ja){
				selectedphenotype_content_text += tokeninput_target.name_ja;
			}else{
				selectedphenotype_content_text += tokeninput_target.name;
			}

			var $selectedphenotype_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).text(selectedphenotype_content_text).appendTo($selectedphenotype_base);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);


			// contents
			var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);

			// super class content
			createOtherContent(results[settings.keySuperclass],{
				title: settings.language[getCurrentLanguage()].superclass,
				classname: CSS_PREFIX+settings.keySuperclass
			}).appendTo($tr);

			// self class content
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).addClass(current_settings.cssSelfContentClass).appendTo($tr);
			if($.isArray(results[current_settings.keySelfclass]) && results[current_settings.keySelfclass].length){
				var $base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).appendTo($td);
				var $title = null;
				if(isString(current_settings.titleSelfclass) && current_settings.titleSelfclass.length){
					$title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTitleClass).text(current_settings.titleSelfclass).appendTo($base);
				}

				var target_arr = [];
				var arr = getTokenInputItems();
				if($.isArray(arr)){
					target_arr = $.grep(arr,function(data){return data.id===results[current_settings.keySelfclass][0].id;});
				}
				if(!isArray(results[settings.keySuperclass])){
					target_arr.push('dummy');
				}

				var data = {
					'target' : $.extend({},tokeninput_target),
					'self' : $.extend({},results[current_settings.keySelfclass][0])
				};

				var $buttons = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonsClass).appendTo($base);
				addExecuteButtons(data,target_arr.length!==0).appendTo($buttons);

				var $content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).appendTo($base);
				var $contentTable = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTableClass).appendTo($content);

				var title_text_arr = [];

				$.each(results[current_settings.keySelfclass], function(){
					var result = this;
					if($title && title_text_arr.length === 0){
						$.each(['id','name'], function(){
							var key = this;
							var value = result[key];
							if(runSearchOptions.hasJA){
								if(isString(result[key+'_ja'])) value = result[key+'_ja'];
							}
							title_text_arr.push(value);
						});
						$title.empty();

						var $title_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','width':'100%'}).appendTo($title);
						var $title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($title_table);
						var $title_td1 = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'4px'}).text(title_text_arr.join(' ')).appendTo($title_tr);
						var $title_td2 = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','width':'20px'}).appendTo($title_tr);
						$('<'+current_settings.nodeName+'>').addClass(current_settings.cssCloseButtonClass).text('X').click(function(){closeMagnificPopup();}).appendTo($title_td2);

					}

					$.each(['id','name','English','definition','synonym'], function(){
						var key = this;
						var value = result[key];
						if(runSearchOptions.hasJA){
							if(isString(result[key+'_ja'])) value = result[key+'_ja'];
							if(key=='English') value = result['name'];
						}else if(key=='English'){
							return;
						}
						var $contentTr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTrClass).appendTo($contentTable);
						$('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentThClass).text(key).appendTo($contentTr);
						$('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTdClass).text(':').appendTo($contentTr);
						var $value_td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTdClass).appendTo($contentTr);
						if(key=='name'){

							$('<a>')
							.addClass(current_settings.cssLinkClass)
							.text(value)
							.attr({'href':'#'})
							.data(OBJECT_KEY, result)
							.css({'display':'inline-block','width':'100%'})
							.click(function(){
								var data = $(this).data(OBJECT_KEY);
								setTimeout(function(){
									runSearch(data.id);
								},0);
								return false;
							})
							.appendTo($value_td);

						}
						else{
							$value_td.text(value);
						}
					});
				});
			}

			// sub class content
			createOtherContent(results[settings.keySubclass],{
				title: settings.language[getCurrentLanguage()].subclass,
				classname:CSS_PREFIX+settings.keySubclass
			}).appendTo($tr);

			openMagnificPopup({
				items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.'+current_settings.cssTableClass },
				type: 'inline',
				modal: false,
				showCloseBtn: false
			});
		}

		function eventKeydown(e){
			//37←, 39→, 38↑, 40↓, 13:enter,
			var $a = $.magnificPopup.instance.content.find(current_settings.nodeName+'.'+current_settings.cssTdClass+' a.'+current_settings.cssLinkClass+'.'+current_settings.cssLinkFocusClass);
			if($a.length){
				if(e.which==13){
					$a.get(0).click();
				}
				else if(e.which==38){
					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseClass;
					var $prev_a = $a.parent(expr).prev(expr).find('a.'+current_settings.cssLinkClass);
					if($prev_a.length){
						$a.removeClass(current_settings.cssLinkFocusClass);
						$prev_a.eq(0).addClass(current_settings.cssLinkFocusClass).get(0).focus();
						e.stopPropagation();
						e.preventDefault();
						return false;
					}
				}
				else if(e.which==40){
					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseClass;
					var $next_a = $a.parent(expr).next(expr).find('a.'+current_settings.cssLinkClass);
					if($next_a.length){
						$a.removeClass(current_settings.cssLinkFocusClass);
						$next_a.eq(0).addClass(current_settings.cssLinkFocusClass).get(0).focus();
						e.stopPropagation();
						e.preventDefault();
						return false;
					}
				}
				else if(e.which==37){
					var expr = current_settings.nodeName+'.'+current_settings.cssTdClass;
					var $prev_a = $a.closest(expr).prev(expr).find('a.'+current_settings.cssLinkClass);
					if($prev_a.length){
						$a.removeClass(current_settings.cssLinkFocusClass);
						$prev_a.eq(0).addClass(current_settings.cssLinkFocusClass).get(0).focus();
						e.stopPropagation();
						e.preventDefault();
						return false;
					}
				}
				else if(e.which==39){
					var expr = current_settings.nodeName+'.'+current_settings.cssTdClass;
					var $next_a = $a.closest(expr).next(expr).find('a.'+current_settings.cssLinkClass);
					if($next_a.length){
						$a.removeClass(current_settings.cssLinkFocusClass);
						$next_a.eq(0).addClass(current_settings.cssLinkFocusClass).get(0).focus();
						e.stopPropagation();
						e.preventDefault();
						return false;
					}
				}
			}
		}

		function closeMagnificPopup(){
			var magnificPopup = $.magnificPopup.instance;
			if(magnificPopup && magnificPopup.close) magnificPopup.close();
		}
		var timeoutID = null;
		function openMagnificPopup(params){
			closeMagnificPopup();

			if(timeoutID){
				clearTimeout(timeoutID);
				timeoutID = null;
			}

			params = $.extend({}, params, {
				callbacks: {
					beforeOpen: function() {
					},
					elementParse: function(item) {
					},
					change: function() {
					},
					resize: function() {
					},
					open: function() {
						if(timeoutID){
							clearTimeout(timeoutID);
							timeoutID = null;
						}
						var current_settings = $(input).data(SETTINGS_KEY);
						var $a = $.magnificPopup.instance.content.find(current_settings.nodeName+'.'+current_settings.cssSelfContentClass+' a.'+current_settings.cssLinkClass);
						if($a.length){
							$a.addClass(current_settings.cssLinkFocusClass);
							$a.get(0).focus();
							$(document.body).on('keydown', eventKeydown);
						}
						else{
							timeoutID = setTimeout(params.callbacks.open,100);
						}
					},
					beforeClose: function() {
					},
					close: function() {
						$(document.body).off('keydown', eventKeydown);
					},
					afterClose: function() {
					},
					updateStatus: function(data) {
					}
				}
			});
			$.magnificPopup.open(params);
		}

		var runSearchOptions = {hasJA:false};
		function runSearch(query,options) {
			runSearchOptions = $.extend({}, runSearchOptions, options || {});

			var current_settings = $(input).data(SETTINGS_KEY);

			var $inlineContent = emptyInlineContent();
			var $loading = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLoadingClass).text(current_settings.loadingText).appendTo($inlineContent);

			openMagnificPopup({
				items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.' + current_settings.cssLoadingClass},
				type: 'inline',
				modal: true,
			});

			var url = computeURL();

			var cache_key = query + url;
			var cached_results = cache.get(cache_key);
			if(cached_results){
				showResults(cached_results);
				if(isFunction(runSearchOptions.callback)){
					runSearchOptions.callback.call(this, true);
				}
			}
			else{
				if(current_settings.url) {
					var ajax_params = {};
					ajax_params.data = {};
					if(url.indexOf("?") > -1) {
						var parts = url.split("?");
						ajax_params.url = parts[0];

						var param_array = parts[1].split("&");
						$.each(param_array, function (index, value) {
							var kv = value.split("=");
							ajax_params.data[kv[0]] = kv[1];
						});
					} else {
						ajax_params.url = url;
					}

					ajax_params.data[current_settings.queryParam] = query;
					ajax_params.type = current_settings.method;
					ajax_params.dataType = current_settings.contentType;
					if (current_settings.crossDomain) {
						ajax_params.dataType = "jsonp";
					}

					ajax_params.success = function(results) {
						cache.add(cache_key, current_settings.jsonContainer ? results[current_settings.jsonContainer] : results);

						showResults(current_settings.jsonContainer ? results[current_settings.jsonContainer] : results);
						if(isFunction(runSearchOptions.callback)){
							runSearchOptions.callback.call(this, true);
						}
					};

					ajax_params.error = function(XMLHttpRequest, textStatus, errorThrown) {
						console.warn(textStatus, errorThrown);
						if(isFunction(runSearchOptions.callback)){
							runSearchOptions.callback.call(this, false);
						}
					};

					if (settings.onSend) {
						settings.onSend(ajax_params);
					}

					$.ajax(ajax_params);
				} else if(current_settings.local_data) {
					var results = $.grep(current_settings.local_data, function (row) {
						return row[current_settings.propertyToSearch].toLowerCase().indexOf(query.toLowerCase()) > -1;
					});

					cache.add(cache_key, results);

					showResults(results);
					if(isFunction(runSearchOptions.callback)){
						runSearchOptions.callback.call(this, true);
					}
				}
			}
		}

		if (isString(url_or_data) || isFunction(url_or_data)) {
			var current_settings = $(input).data(SETTINGS_KEY);
			current_settings.url = url_or_data;
			var url = computeURL();
			if (current_settings.crossDomain === undefined && isString(url)) {
				if(url.indexOf("://") === -1) {
					current_settings.crossDomain = false;
				} else {
					current_settings.crossDomain = (location.href.split(/\/+/g)[1] !== url.split(/\/+/g)[1]);
				}
			}
		} else if (isObject(url_or_data)) {
			current_settings.local_data = url_or_data;
		}

		var tokeninput_settings = $(input).data(TOKENINPUT_SETTINGS_KEY);
		var tokeninput_target = null;
		var tokeninput_array = null;
		var tokeninput_target_results = null;

		if(isObject(tokeninput_settings) && tokeninput_settings.classes) {
			var tokeninput_classes = tokeninput_settings.classes;
			if(isObject(tokeninput_classes) && isString(tokeninput_classes['tokenList']) && isString(tokeninput_classes['token'])){
				var selector = 'ul.'+tokeninput_classes['tokenList']+'>li.'+tokeninput_classes['token'];//+'>p';

				$(document).on('click',selector,function(){
					var click_text = '';
					if($(this).get(0).nodeName.toLowerCase()==='li'){
						click_text = $(this).children('p').text();
					}
					else if($(this).get(0).nodeName.toLowerCase()==='p'){
						click_text = $(this).text();
					}
					else if($(this).get(0).nodeName.toLowerCase()==='span'){
						click_text = $(this).parent('li').children('p').text();
					}

					var tokenInputItem = getTokenInputItemFromName(click_text);
					if(tokenInputItem){
						tokeninput_target = null;
						tokeninput_target_results = null;
						runSearch(tokenInputItem.id,{hasJA:hasJA(tokenInputItem.name)});
					}
					else{
//						console.warn(click_text,tokeninput_array);
					}
					return false;
				});


			}
		}
	};

}(jQuery));

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

		disabledTokenIds : ['HP:0000118'],

		cssInlineContentClass: CSS_PREFIX+'inline-content',
		cssTableClass: CSS_PREFIX+'table',
		cssTrClass: CSS_PREFIX+'tr',
		cssTdClass: CSS_PREFIX+'td',

		cssBaseClass: CSS_PREFIX+'base',
		cssTopBarClass: CSS_PREFIX+'top-bar',
		cssBottomBarClass: CSS_PREFIX+'bottom-bar',
		cssContentClass: CSS_PREFIX+'content',
		cssLinkBaseClass: CSS_PREFIX+'link-base',
		cssLinkClass: CSS_PREFIX+'link',
		cssLinkFocusClass: CSS_PREFIX+'link-focus',
		cssTokenClass: CSS_PREFIX+'token',
		cssTokenListClass: CSS_PREFIX+'token-list',

		cssSelfContentClass: CSS_PREFIX+'self-content',
		cssOtherContentClass: CSS_PREFIX+'other-content',
		cssCloseButtonClass: CSS_PREFIX+'close-button',

		cssSelectedPhenotypeClass: CSS_PREFIX+'selectedphenotype',

//		cssButtonPrefixClass: CSS_PREFIX+'button-',
		cssButtonDisabledClass: CSS_PREFIX+'button-disabled',
		cssButtonAddClass: CSS_PREFIX+'button-add',
		cssButtonReplaceClass: CSS_PREFIX+'button-replace',

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
//				selectedphenotype: '選択した症状',
				selectedphenotype: '患者の徴候および症状',
				replace : '置換',
				add : '追加',
				jpn : 'JPN',
				eng : 'ENG',
				revert : '元に戻す',
				ok : 'OK',
				cancel : 'Cancel',
				id : 'id',
				name : 'name',
				english : 'English',
				definition : 'definition',
				synonym : 'synonym'
			},
			'en' : {
				superclass : 'superclass',
				subclass : 'subclass',
//				selectedphenotype: 'selected phenotype',
				selectedphenotype: 'patient\’s signs and symptoms',
				replace : 'Replace',
				add : 'Add',
				jpn : 'JPN',
				eng : 'ENG',
				revert : 'revert',
				ok : 'OK',
				cancel : 'Cancel',
				id : 'id',
				name : 'name',
				english : 'English',
				definition : 'definition',
				synonym : 'synonym'
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
		var tokeninput_settings = $(input).data(TOKENINPUT_SETTINGS_KEY);
		var tokeninput_classes = tokeninput_settings.classes;
		var current_settings = $(input).data(SETTINGS_KEY);

		function computeURL() {
			return isFunction(current_settings.url) ? settings.url.call(current_settings) : current_settings.url;
		}

		function getOriginalTokenInputNodes(){
//			return $(input).tokenInput('get');
			return $('ul.'+tokeninput_classes['tokenList']).not('.'+current_settings.cssTokenListClass).children('li.'+tokeninput_classes['token']).not('.'+current_settings.cssTokenClass).toArray();
		}

		function getOriginalTokenInputItems(){
//			console.log('call getOriginalTokenInputItems()');
//			return $(input).tokenInput('get');
			return $.map($(input).tokenInput('get'), function(data){
				return $.extend({},data);
			});
		}
		function removeOriginalTokenInputItems(){
//			console.log('call removeOriginalTokenInputItems()');
			return $(input).tokenInput('clear');
		}
		function addOriginalTokenInputItem(){
//			console.log('start addOriginalTokenInputItem()');
//			return $(input).tokenInput('add',token);
			var tokenInputItems = getTokenInputItems();
//			var originalTokenInputItems = getOriginalTokenInputItems();
/*
			var addTokenInputItems = [];
			$.each(tokenInputItems, function(){
				var tokenInputItem = this;
				if($.grep(originalTokenInputItems,function(data){ return data.id===tokenInputItem.id; }).length === 0){
					addTokenInputItems.push(tokenInputItem);
				}
			});
*/
//			console.log(tokenInputItems,originalTokenInputItems);
			if(isArray(tokenInputItems)){
//				console.log(getOriginalTokenInputItems());
				removeOriginalTokenInputItems();
//				console.log(getOriginalTokenInputItems());
//				setTimeout(function(){
					$.each(tokenInputItems,function(){
//						console.log(isObject(this),this);
						$(input).tokenInput('add',this);
					});
//				},0);
			}
//			console.log('end   addOriginalTokenInputItem()');
		}
		function getOriginalTokenInputItemFromName(hpo_name){
			var tokenInputItems = getOriginalTokenInputItems();
			var target_arr = [];
			if($.isArray(tokenInputItems)){
				target_arr = $.grep(tokenInputItems,function(data){return data.name===hpo_name;});
			}
			return target_arr.length>0 ? target_arr[0] : null;
		}

		function getTokenInputNodes(){
//			return $(input).tokenInput('get');
			return $('ul.'+tokeninput_classes['tokenList']+'.'+current_settings.cssTokenListClass+'>li.'+tokeninput_classes['token']+'.'+current_settings.cssTokenClass).toArray();
		}

		function getTokenInputItems(){
			return $.map(getTokenInputNodes(),function(data){ return $(data).data(OBJECT_KEY); });
		}

		function addTokenInputItem(token,selectedToken){
			var name = token.name;
			if(!isBoolean(selectedToken)) selectedToken = false;

			var $li = $('<li>').addClass(tokeninput_classes['token']).addClass(current_settings.cssTokenClass).data(OBJECT_KEY, token).appendTo($('ul.'+current_settings.cssTokenListClass));
			$('<p>').text(name).data(OBJECT_KEY, token).appendTo($li);
			$('<span>').css({'display':'inline-block'}).addClass(tokeninput_classes['tokenDelete']).text('×').data(OBJECT_KEY, token).appendTo($li).on('click', function(e){

				var data = $(this).data(OBJECT_KEY) || {};
				$(this).parent('li').remove();

				if(isObject(runSearchOptions)){
					if(isArray(runSearchOptions.tokenInputItems)) runSearchOptions.tokenInputItems = $.grep(runSearchOptions.tokenInputItems || [],function(token){return token.id!==data.id;});
					if(isArray(runSearchOptions.tokenInputNodes)) runSearchOptions.tokenInputNodes = getTokenInputNodes();
				}

				changeStateAddOrReplace();
				e.preventDefault();
				e.stopPropagation();
				return false;
			});
			if(isObject(selectedToken) && selectedToken.id && selectedToken.id===token.id){
				$li.addClass(tokeninput_classes['selectedToken']);
			}else if(isBoolean(selectedToken) && selectedToken){
				$li.addClass(tokeninput_classes['selectedToken']);
			}

			return $li;
		}
		function removeTokenInputItems(){
//			return $(input).tokenInput('clear');
			$('ul.'+current_settings.cssTokenListClass).empty();
		}
		function getSelectedTokenInputItems(){
			return $(getTokenInputNodes()).filter('.'+tokeninput_classes['selectedToken']).toArray();
		}
		function clearSelectedTokenInputItems(){
			return $(getSelectedTokenInputItems()).removeClass(tokeninput_classes['selectedToken']);
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
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).addClass(current_settings.cssOtherContentClass); //.appendTo($tr);
			if($.isArray(values) && values.length){
				var $base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssOtherContentClass).appendTo($td);
				if(isString(options.classname)) $base.addClass(options.classname);
				if(isString(options['title']) && options['title'].length){
					var $title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).text(options['title']).appendTo($base);
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

		function changeStateAddOrReplace(){
			var $selectedToken = $(getSelectedTokenInputItems());
			var tokenInputItems = getTokenInputItems();
			var tokenInputItemsHash = {};
			if(isArray(tokenInputItems)){
				$.each(tokenInputItems, function(){
					var tokenInputItem = this;
					tokenInputItemsHash[tokenInputItem.id] = tokenInputItem;
				});
			}

			var $buttonAdd = $('button.'+current_settings.cssButtonAddClass);
			$buttonAdd.each(function(){
				var $button = $(this);
				var data = $button.data(OBJECT_KEY);
				var exists_data = $.grep(current_settings.disabledTokenIds, function(id){
					return id===data.self.id;
				}).length > 0 ? true : false;
				if(isObject(tokenInputItemsHash[data.self.id]) || exists_data ){
					$button.addClass(current_settings.cssButtonDisabledClass);
				}
				else{
					$button.removeClass(current_settings.cssButtonDisabledClass);
				}
			});

			var $buttonReplace = $('button.'+current_settings.cssButtonReplaceClass);

			if($selectedToken && $selectedToken.length > 0){
				$buttonReplace.removeClass(current_settings.cssButtonDisabledClass);

				$buttonReplace.each(function(){
					var $button = $(this);
					var data = $button.data(OBJECT_KEY);
					var exists_data = $.grep(current_settings.disabledTokenIds, function(id){
						return id===data.self.id;
					}).length > 0 ? true : false;
					if(isObject(tokenInputItemsHash[data.self.id]) || exists_data) $button.addClass(current_settings.cssButtonDisabledClass);
				});
			}
			else{
				$buttonReplace.addClass(current_settings.cssButtonDisabledClass);
			}


//				if(disabled) $button.addClass(current_settings.cssButtonDisabledClass);

//current_settings.cssButtonAddClass
//current_settings.cssButtonReplaceClass
		}

		function executionAddOrReplace(e){
			var $button = $(this);
			e.preventDefault();
			e.stopPropagation();
			if($button.hasClass(current_settings.cssButtonDisabledClass)) return false;
			var params = $button.data(OBJECT_KEY) || {};

			var new_token = {id: params.self.id, name: params.self.id+' '+params.self.name};
			if(runSearchOptions.hasJA && isString(params.self.name_ja)) new_token['name'] = params.self.id+' '+params.self.name_ja;

			if(params.exec==='add'){
				addTokenInputItem(new_token);
				runSearchOptions.tokenInputItems.push(new_token);

//				$button.parent(current_settings.nodeName+'.'+current_settings.cssButtonBaseClass).find('button').off('click',executionAddOrReplace).css({opacity:0.2,cursor:'default'});
			}
			else if(params.exec==='replace'){
				var $selectedToken = $('li.'+tokeninput_classes['selectedToken']+'.'+current_settings.cssTokenClass);
				var selectedToken = null;
				if($selectedToken && $selectedToken.length) selectedToken = $selectedToken.data(OBJECT_KEY);
//				console.log('selectedToken',selectedToken);

				var new_arr = [];
				var new_index = -1;
				if(isObject(selectedToken)){

					var arr = getTokenInputItems();
					if($.isArray(arr)){
						$.each(arr, function(index){
							if(this.id===selectedToken.id){
								new_arr.push(new_token);
								new_index = index;
							}
							else{
								new_arr.push(this);
							}
						});
					}
				}
				if(new_arr.length){

//					tokeninput_target_results = $.extend({},results);
					tokeninput_target = $.extend({},params.self);
					runSearchOptions.tokenInputItems = [];
					$.each(new_arr, function(){runSearchOptions.tokenInputItems.push(this);});

					removeTokenInputItems();
					$.each(new_arr, function(index){
//						addTokenInputItem(this,params.self);
						addTokenInputItem(this,new_index === index);
					});
				}
//				closeMagnificPopup();
			}
			changeStateAddOrReplace();
			return false;
		}

		function addExecuteButtons(data,disabled){
			if(!isBoolean(disabled)) disabled = disabled ? true : false;
//			disabled = false;

			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);

			$.each(['add','replace'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-primary').addClass(key=='add'?current_settings.cssButtonAddClass:current_settings.cssButtonReplaceClass).data(OBJECT_KEY,  $.extend({},data,{'exec' : key.toLowerCase()})   ).text(settings.language[getCurrentLanguage()][key]).appendTo($button_base);
/*
				if(!disabled){
					$button.on('click',executionAddOrReplace);
				}else{
					$button.css({opacity:0.2,cursor:'default'});
				}
*/
				$button.on('click',executionAddOrReplace);
//				if(disabled) $button.addClass(current_settings.cssButtonDisabledClass);
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

		function executionOKCancel(){
			var $button = $(this);
//			console.log('start executionOKCancel()',getTokenInputItems(),getOriginalTokenInputItems());
			var params = $button.data(OBJECT_KEY) || {};
			if(params.exec==='ok'){
//					console.log('call addOriginalTokenInputItem()',getTokenInputItems(),getOriginalTokenInputItems());
					addOriginalTokenInputItem();
//					console.log('back addOriginalTokenInputItem()',getTokenInputItems(),getOriginalTokenInputItems());
			}
			setTimeout(function(){
				closeMagnificPopup();
			},100);
//			console.log('end   executionOKCancel()',getTokenInputItems(),getOriginalTokenInputItems());
			return;
		}

		function addOKCancelButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			var language = settings.language[getCurrentLanguage()];
			$.each(['ok','cancel'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn').addClass(key=='ok'?'btn-primary':'btn-default').data(OBJECT_KEY,  $.extend({},{'exec' : key.toLowerCase()})   ).text(language[key] ? language[key] : key).appendTo($button_base);
				$button.on('click',executionOKCancel);
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


//			console.log(tokeninput_target);
			if(!tokeninput_target){
				tokeninput_target_results = $.extend({},results);
				tokeninput_target = $.extend({},results[current_settings.keySelfclass][0]);
			}

			var $inlineContent = emptyInlineContent();
			var $table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).appendTo($inlineContent);
			$table.css({'margin-top':'90px'});

			//selected phenotype
			var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
//			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
			var $selectedphenotype_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssSelectedPhenotypeClass).appendTo($td);
			var $selectedphenotype_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).appendTo($selectedphenotype_base);
			$selectedphenotype_title.empty();
			var $selectedphenotype_title_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','empty-cells':'hide','width':'100%'}).appendTo($selectedphenotype_title);
			var $selectedphenotype_title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($selectedphenotype_title_table);
//			var $selectedphenotype_title_td_left = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'4px'}).appendTo($selectedphenotype_title_tr);
//			$selectedphenotype_title_td_left.text(settings.language[getCurrentLanguage()]['selectedphenotype']);
			var $selectedphenotype_title_td_center = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'center'}).appendTo($selectedphenotype_title_tr);
//			addLanguageButtons().appendTo($selectedphenotype_title_td_center);
			$selectedphenotype_title_td_center.text(settings.language[getCurrentLanguage()]['selectedphenotype']);
//			var $selectedphenotype_title_td_right = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','width':'20px','padding-left':'4px'}).appendTo($selectedphenotype_title_tr);
//			addRevertButton().appendTo($selectedphenotype_title_td_right);



/*
			var selectedphenotype_content_text = tokeninput_target.id+' ';
			if(runSearchOptions.hasJA && tokeninput_target.name_ja){
				selectedphenotype_content_text += tokeninput_target.name_ja;
			}else{
				selectedphenotype_content_text += tokeninput_target.name;
			}
			var $selectedphenotype_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).text(selectedphenotype_content_text).appendTo($selectedphenotype_base);
*/

			if(runSearchOptions.tokenInputItems && runSearchOptions.tokenInputItems.length){
				if(isObject(tokeninput_settings) && isObject(tokeninput_settings.classes) && isString(tokeninput_settings.classes['tokenList']) && isString(tokeninput_settings.classes['token'])) {
					var $selectedphenotype_content = $('<ul>').css({'min-height':'30px'}).addClass(tokeninput_classes['tokenList']).addClass(current_settings.cssTokenListClass).appendTo($selectedphenotype_base).on('click', function(e){
						if($(e.target).hasClass(current_settings.cssTokenListClass)){
//							console.log(e);
							clearSelectedTokenInputItems();
							if(isObject(runSearchOptions) && isArray(runSearchOptions.tokenInputNodes)) runSearchOptions.tokenInputNodes = getTokenInputNodes();
							changeStateAddOrReplace();
							e.preventDefault();
							e.stopPropagation();
							return false;
						}
					});;
					runSearchOptions.tokenInputItems.forEach(function(tokenInputItem,index){
/*
						var $selectedphenotype_content_item = $('<li>').addClass(tokeninput_classes['token']).addClass(current_settings.cssTokenClass).data(OBJECT_KEY, tokenInputItem).appendTo($selectedphenotype_content);

						if(tokeninput_target.id===tokenInputItem.id) $selectedphenotype_content_item.addClass(tokeninput_classes['selectedToken']);

						$('<p>').text(tokenInputItem.name).data(OBJECT_KEY, tokenInputItem).appendTo($selectedphenotype_content_item);
						$('<span>').css({'display':'inline-block'}).addClass(tokeninput_classes['tokenDelete']).text('×').data(OBJECT_KEY, tokenInputItem).appendTo($selectedphenotype_content_item).on('click', function(e){
							$(this).parent('li').remove();
							changeStateAddOrReplace();
							e.preventDefault();
							e.stopPropagation();
							return false;
						});
*/

						var selectedToken = isArray(runSearchOptions.tokenInputNodes) && $(runSearchOptions.tokenInputNodes).eq(index).hasClass(tokeninput_classes['selectedToken']) ? true : false;
//						console.log(selectedToken);

//						addTokenInputItem(tokenInputItem,tokeninput_target);
						addTokenInputItem(tokenInputItem,selectedToken);
					});
				}
				else{
					runSearchOptions.tokenInputItems.forEach(function(tokenInputItem){
						var $selectedphenotype_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).text(tokenInputItem.name).appendTo($selectedphenotype_base);
					});
				}
			}



			var $selectedphenotype_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBottomBarClass).appendTo($selectedphenotype_base);
			$selectedphenotype_title.empty();

			var $selectedphenotype_title_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','empty-cells':'hide','width':'100%'}).appendTo($selectedphenotype_title);
			var $selectedphenotype_title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($selectedphenotype_title_table);
//			var $selectedphenotype_title_td_left = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'4px'}).appendTo($selectedphenotype_title_tr);
			var $selectedphenotype_title_td_center = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'center'}).appendTo($selectedphenotype_title_tr);
//			addLanguageButtons().appendTo($selectedphenotype_title_td_center);
			addOKCancelButtons().appendTo($selectedphenotype_title_td_center);
//			var $selectedphenotype_title_td_right = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','padding-left':'4px'}).appendTo($selectedphenotype_title_tr);
//			addOKCancelButtons().appendTo($selectedphenotype_title_td_right);




//			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);








			// contents
			var $table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).appendTo($inlineContent);
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
					$title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).text(current_settings.titleSelfclass).appendTo($base);
				}

				var target_arr = [];
				var arr = getTokenInputItems();
				if($.isArray(arr)){
					target_arr = $.grep(arr,function(data){return data.id===results[current_settings.keySelfclass][0].id;});
				}
				if(!isArray(results[settings.keySuperclass]) || results[settings.keySuperclass].length===0){
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

				var language = settings.language[getCurrentLanguage()];

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
//						$('<'+current_settings.nodeName+'>').addClass(current_settings.cssCloseButtonClass).text('X').click(function(){closeMagnificPopup();}).appendTo($title_td2);

						addLanguageButtons().appendTo($title_td2);

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
						var label = language[key.toLowerCase()] ? language[key.toLowerCase()] : key;
						var $contentTr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTrClass).appendTo($contentTable);
						$('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentThClass).text(label).appendTo($contentTr);
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

			changeStateAddOrReplace();

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
				enableEscapeKey: false,
				closeOnBgClick: false,
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
			if(isObject(options) && isObject(runSearchOptions)){
				if(options.tokenInputItems && runSearchOptions.tokenInputItems) delete runSearchOptions.tokenInputItems;
				if(options.tokenInputNodes && runSearchOptions.tokenInputNodes) delete runSearchOptions.tokenInputNodes;
			}
			runSearchOptions = $.extend({}, runSearchOptions, options || {});


			var $inlineContent = emptyInlineContent();
//			var $loading = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLoadingClass).text(current_settings.loadingText).appendTo($inlineContent);
//			var $loading = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLoadingClass).appendTo($inlineContent);
//			$('<span>').text(current_settings.loadingText).appendTo($loading);

			var $table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).addClass(current_settings.cssLoadingClass).appendTo($inlineContent);
			var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).css({'vertical-align':'middle'}).appendTo($tr);
			$td.text(current_settings.loadingText);

			openMagnificPopup({
				items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.' + current_settings.cssLoadingClass},
				type: 'inline',
				modal: true,
			});
//			return;

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

//		var tokeninput_settings = $(input).data(TOKENINPUT_SETTINGS_KEY);
		var tokeninput_target = null;
		var tokeninput_array = null;
		var tokeninput_target_results = null;

		if(isObject(tokeninput_settings) && tokeninput_settings.classes) {
			if(isObject(tokeninput_classes) && isString(tokeninput_classes['tokenList']) && isString(tokeninput_classes['token'])){
				var selector = 'ul.'+tokeninput_classes['tokenList']+'>li.'+tokeninput_classes['token'];//+'>p';

				$(document).on('click',selector,function(e){
					var click_text = '';
					var $li_node;
					if($(this).get(0).nodeName.toLowerCase()==='li'){
						$li_node = $(this);
						click_text = $li_node.children('p').text();
					}
					else if($(this).get(0).nodeName.toLowerCase()==='p'){
						$li_node = $(this).parent('li');
						click_text = $(this).text();
					}
					else if($(this).get(0).nodeName.toLowerCase()==='span'){
						$li_node = $(this).parent('li');
						click_text = $li_node.children('p').text();
					}

					var tokenInputItems;
					var tokenInputNodes;
					var tokenInputItem;
//					if($li_node){
//						console.log($li_node.hasClass(current_settings.cssTokenClass));
//					}
					if($li_node){
						if($li_node.hasClass(current_settings.cssTokenClass)){
							tokenInputItems = getTokenInputItems();
							tokenInputNodes = getTokenInputNodes();
							tokenInputItem =  getTokenInputItemFromName(click_text);
						}
						else{
							tokenInputItems = getOriginalTokenInputItems();
							tokenInputNodes = getOriginalTokenInputNodes();
							tokenInputItem =  getOriginalTokenInputItemFromName(click_text);
						}
						$(tokenInputNodes).removeClass(tokeninput_classes['selectedToken']);
						$li_node.addClass(tokeninput_classes['selectedToken']);
					}

//					var tokenInputItem = getTokenInputItemFromName(click_text);
					if(tokenInputItem){
						tokeninput_target = null;
						tokeninput_target_results = null;
						var options = {
							hasJA: hasJA(tokenInputItem.name)
						};
						if(tokenInputItems) options.tokenInputItems = tokenInputItems;
						if(tokenInputNodes) options.tokenInputNodes = tokenInputNodes;
						runSearch(tokenInputItem.id,options);
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

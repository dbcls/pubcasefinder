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

		defaultTokenId : 'HP:0000118',
		disabledTokenIds : ['HP:0000118'],

		cssInlineContentClass: CSS_PREFIX+'inline-content',
		cssInlineContentBaseClass: CSS_PREFIX+'inline-content-base',

		cssTokenInputContentBaseClass: CSS_PREFIX+'tokeninput-content-base',
		cssClassContentBaseClass: CSS_PREFIX+'class-content-base',
		cssWebGLContentBaseClass: CSS_PREFIX+'webgl-content-base',

		cssTableClass: CSS_PREFIX+'table',
		cssTrClass: CSS_PREFIX+'tr',
		cssTdClass: CSS_PREFIX+'td',

		cssBaseClass: CSS_PREFIX+'base',
		cssTopBarClass: CSS_PREFIX+'top-bar',
		cssBottomBarClass: CSS_PREFIX+'bottom-bar',
		cssContentClass: CSS_PREFIX+'content',
		cssLinkBaseRowClass: CSS_PREFIX+'link-base-row',
		cssLinkBaseClass: CSS_PREFIX+'link-base',
		cssLinkClass: CSS_PREFIX+'link',
		cssLinkNumberClass: CSS_PREFIX+'link-number',
		cssLinkFocusClass: CSS_PREFIX+'link-focus',
		cssTokenClass: CSS_PREFIX+'token',
		cssTokenListClass: CSS_PREFIX+'token-list',

		cssSelfContentClass: CSS_PREFIX+'self-content',
		cssOtherContentClass: CSS_PREFIX+'other-content',
		cssCloseButtonClass: CSS_PREFIX+'close-button',

		cssCheckboxGroupClass: CSS_PREFIX+'checkbox-group',
		cssProgressClass: CSS_PREFIX+'progress',

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

		cssWebGLContentClass: CSS_PREFIX+'webgl-content',
//		cssWebGLSpeechBalloonBaseClass: CSS_PREFIX+'webgl-speechballoon-base',
//		cssWebGLSpeechBalloonContentClass: CSS_PREFIX+'webgl-speechballoon-content',
		cssFMAListContentClass: CSS_PREFIX+'fmalist-content',
		cssFMAListContentSelectClass: CSS_PREFIX+'fmalist-content-select',
		cssFMAListContentHoverClass: CSS_PREFIX+'fmalist-content-hover',
		cssHPOListContentClass: CSS_PREFIX+'hpolist-content',

		cssWebGLSwitchContentClass: CSS_PREFIX+'webgl-switch-content',
		cssLanguageChangeClass: CSS_PREFIX+'language-change',
		cssWebGLHomeContentClass: CSS_PREFIX+'webgl-home-content',

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
				clear : 'Clear',
				close : 'Close',

				id : 'id',
				name : 'name',
				english : 'English',
				definition : 'definition',
				synonym : 'synonym',

				phenotouch : 'PhenoTouch',
				webgltitle : '身体各部位を選択',
				fmalisttitle : 'Select proper parts you inducated.',
//				hpolisttitle : 'Add phenotype related to selected parts.',
				hpolisttitle : '',

				bone : 'Bone',
				muscle : 'Muscle',
				vessel : 'Vessel',
				internal : 'Internal',
				other : 'Other',

				fmaid : 'FMA ID',
				fmaname : 'Name',
				'#ofphenotypes' : '# of phenotypes',
				color : 'Color',
				hide : 'Hide',
				hpoid : 'ID',
				hponame : 'Name'
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
				clear : 'Clear',
				close : 'Close',

				id : 'id',
				name : 'name',
				english : 'English',
				definition : 'definition',
				synonym : 'synonym',

				phenotouch : 'PhenoTouch',
				webgltitle : 'Touch body parts',
				fmalisttitle : 'Select proper parts you inducated.',
//				hpolisttitle : 'Add phenotype related to selected parts.',
				hpolisttitle : '',

				bone : 'Bone',
				muscle : 'Muscle',
				vessel : 'Vessel',
				internal : 'Internal',
				other : 'Other',

				fmaid : 'FMA ID',
				fmaname : 'Name',
				'#ofphenotypes' : '# of phenotypes',
				color : 'Color',
				hide : 'Hide',
				hpoid : 'ID',
				hponame : 'Name'
			}
		},
		okcancelButtonsAlign : 'right',
		clearButtonAlign : 'left',

		inputNodeName: 'textarea',
		inputId : 'popup-hierarchy-hpo'

//		,use_segments: ['bone','muscle','vessel','internal','other']
//		,use_segments: ['internal','bone','muscle','vessel','other']
		,use_segments: ['internal','bone','muscle']
		,id_regexp : new RegExp("^(HP:[0-9]+)(.*)")
		,obj_ext : '.obj'
//		,obj_ext : '.ogz'
		,obj_url : '/phenotouch/objs/'
	};

	var TOKENINPUT_SETTINGS_KEY = 'settings';
	var TOKENINPUT_ITEM_SETTINGS_KEY = 'tokeninput';

	var SKIN = {
		FMAID : 'FMA7163',
		OPACITY : 0.2,
		DEFAULT_OPACITY : 0.1
	};

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
	isEmpty = function(value, allowEmptyString) {
		return (value === null) || (value === undefined) || (!allowEmptyString ? value === '' : false) || (isArray(value) && value.length === 0);
	},
	isDefined = function(value) {
		return typeof value !== 'undefined';
	},
	hasJA = function( str ) {
		return ( str.match(/[\u30a0-\u30ff\u3040-\u309f\u3005-\u3006\u30e0-\u9fcf]+/) )? true : false
	};

	var methods = {
		init: function(url_or_data_or_function, options) {
			var settings = $.extend(true,{}, DEFAULT_SETTINGS, options || {});
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


	var PopupRelationHPO = function (input, url_or_data_or_function, settings) {

		var cache = new $.TokenList.Cache();
		var tokeninput_settings = $.extend(true,{},$(input).data(TOKENINPUT_SETTINGS_KEY) || {});
		if(tokeninput_settings.prePopulate) delete tokeninput_settings.prePopulate;
//		console.log(tokeninput_settings);
		var tokeninput_classes = tokeninput_settings.classes;
		var current_settings = $(input).data(SETTINGS_KEY);

//		var __threeBitsRenderer;
		var __isFirstThreeBitsRenderer = true;
		var __webglResizeTimeoutID = null;


		function computeURL() {
			return isFunction(current_settings.url) ? settings.url.call(current_settings) : current_settings.url;
		}

		function getOriginalTokenInputItemNodes(){
			return $('ul.'+tokeninput_classes['tokenList']).not('.'+current_settings.cssTokenListClass).children('li.'+tokeninput_classes['token']).not('.'+current_settings.cssTokenClass).toArray();
		}

		function getOriginalTokenInputItems(){
			return $.map($(input).tokenInput('get'), function(data){
				return $.extend(true, {},data);
			});
		}
		function removeOriginalTokenInputItems(){
			return $(input).tokenInput('clear');
		}
		function addOriginalTokenInputItem(){
			var tokenInputItems = getTokenInputItems();
			if(isArray(tokenInputItems)){
				removeOriginalTokenInputItems();
				$.each(tokenInputItems,function(){
					var temp = $.extend(true, {},this);
					if(isObject(temp) && isString(temp.id) && current_settings.id_regexp.test(temp.id)){
						temp.id = RegExp.$1;
					}
					if(hasJA(temp.name)) temp.id += '_ja';
					$(input).tokenInput('add',temp);
				});
			}
		}
		function getOriginalTokenInputItemFromName(hpo_name){
			var tokenInputItems = getOriginalTokenInputItems();
			var target_arr = [];
			if($.isArray(tokenInputItems)){
				target_arr = $.grep(tokenInputItems,function(data){return data.name===hpo_name;});
			}
			return target_arr.length>0 ? target_arr[0] : null;
		}

		function getTokenInputItemNodes(){
//			return $(input).tokenInput('get');
			return $('ul.'+tokeninput_classes['tokenList']+'.'+current_settings.cssTokenListClass+'>li.'+tokeninput_classes['token']+'.'+current_settings.cssTokenClass).toArray();
		}

		function getTokenInputItems(){
//			return $.map(getTokenInputItemNodes(),function(data){ return $(data).data(OBJECT_KEY); });
			return $.map(getTokenInputItemNodes(),function(data){ return $(data).data(TOKENINPUT_ITEM_SETTINGS_KEY); });
/*
//			return getTokenInputElement().tokenInput('get');
			try{
				return $.map(getTokenInputElement().tokenInput('get'), function(data){
					return $.extend(true, {},data);
				});
			}catch(e){
				return [];
			}
*/
		}

		function getTokenInputElement(){
			return $(current_settings.inputNodeName+'#'+current_settings.inputId);
		}

		function _addTokenInputItem(token,selectedToken){
//			console.log('_addTokenInputItem',token,selectedToken);
			if(!isBoolean(selectedToken)) selectedToken = false;
			var $li = $(current_settings.nodeName+'.'+current_settings.cssSelectedPhenotypeClass+ ' ul.'+tokeninput_classes['tokenList']+'.'+current_settings.cssTokenListClass+'>li.'+tokeninput_classes['token']).not('.'+current_settings.cssTokenClass).addClass(current_settings.cssTokenClass);
			if(isObject(selectedToken) && selectedToken.id && selectedToken.id===token.id){
				$li.addClass(tokeninput_classes['selectedToken']);
			}else if(isBoolean(selectedToken) && selectedToken){
				clearSelectedTokenInputItems();
				$li.addClass(tokeninput_classes['selectedToken']);
			}
/*
			if($li.length){
				var data = $li.data(TOKENINPUT_ITEM_SETTINGS_KEY);
				console.log(data);
				if(isObject(data) && data.id_suffix===undefined && isString(data.id) && current_settings.id_regexp.test(data.id)){
					data.id_suffix = RegExp.$2;
					data.id = RegExp.$1;
					$li.data(TOKENINPUT_ITEM_SETTINGS_KEY,data);
					console.log(data);
				}
			}
*/
			return $li;
		}

		function addTokenInputItem(token,selectedToken){
			var name = token.name;

			getTokenInputElement().tokenInput('add',token);
/*
			var $li = $(current_settings.nodeName+'.'+current_settings.cssSelectedPhenotypeClass+ ' ul.'+tokeninput_classes['tokenList']+'.'+current_settings.cssTokenListClass+'>li.'+tokeninput_classes['token']).not('.'+current_settings.cssTokenClass).addClass(current_settings.cssTokenClass);
			if(isObject(selectedToken) && selectedToken.id && selectedToken.id===token.id){
				$li.addClass(tokeninput_classes['selectedToken']);
			}else if(isBoolean(selectedToken) && selectedToken){
				$li.addClass(tokeninput_classes['selectedToken']);
			}
			return $li;
*/
			return _addTokenInputItem(token,selectedToken);

/*
			var $li = $('<li>').addClass(tokeninput_classes['token']).addClass(current_settings.cssTokenClass).data(OBJECT_KEY, token).appendTo($('ul.'+current_settings.cssTokenListClass));
			$('<p>').text(name).data(OBJECT_KEY, token).appendTo($li);
			$('<span>').css({'display':'inline-block'}).addClass(tokeninput_classes['tokenDelete']).text('×').data(OBJECT_KEY, token).appendTo($li).on('click', function(e){

				var data = $(this).data(OBJECT_KEY) || {};
				$(this).parent('li').remove();

				if(isObject(runSearchOptions)){
					if(isArray(runSearchOptions.tokenInputItems)) runSearchOptions.tokenInputItems = $.grep(runSearchOptions.tokenInputItems || [],function(token){return token.id!==data.id;});
					if(isArray(runSearchOptions.tokenInputItemNodes)) runSearchOptions.tokenInputItemNodes = getTokenInputItemNodes();
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
*/


		}
		function removeTokenInputItems(){
//			return $(input).tokenInput('clear');
//			$('ul.'+current_settings.cssTokenListClass).empty();
			return getTokenInputElement().tokenInput('clear');
		}
		function getSelectedTokenInputItems(){
			return $(getTokenInputItemNodes()).filter('.'+tokeninput_classes['selectedToken']).toArray();
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

		var click_timeoutID = null;
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

				$content.css({'display':'table','width':'100%','border-spacing':'0'});

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
					var $number_html;
					if(runSearchOptions.hasJA && isString(this.name_ja)) text = this.name_ja;

					if(isNumeric(this.count)){
						if(options.formatNumber){
//							$number_html = $('<div>').addClass(current_settings.cssLinkNumberClass);
//							$('<span>').text(this.count).appendTo($number_html);
							$number_html = $('<span>').addClass(current_settings.cssLinkNumberClass).text(this.count);
						}
						else{
							text += ' ('+this.count+')';
						}
					}

					var data = {
						'target' : $.extend(true, {},tokeninput_target),
						'self' : $.extend(true, {},this)
					};

////					var $link_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLinkBaseClass).appendTo($content);
//					var $link_base_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLinkBaseRowClass).appendTo($content);

//					var $link_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLinkBaseClass).appendTo($link_base_base);
					var $link_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssLinkBaseClass).css({'display':'table-row'}).appendTo($content);

					//superclass
					if(isString(options.classname) && options.classname === CSS_PREFIX+current_settings.keySubclass){
						addExecuteButtons(data, existsTokenInputItemFromID(this.id)).appendTo($link_base).css(add_css);
						if($number_html) $number_html.appendTo($('<'+current_settings.nodeName+'>').css({'display':'table-cell','vertical-align':'top','text-align':'right','width':'1px'}).appendTo($link_base));
					}

					var $a_base = $('<'+current_settings.nodeName+'>').css({'display':'table-cell'}).appendTo($link_base);

					var $a = $('<a>')
					.addClass(current_settings.cssLinkClass)
//					.text(text)
					.attr({'href':'#'})
					.data(OBJECT_KEY, this)
					.click(function(){
						var data = $(this).data(OBJECT_KEY);

						if(false){
							if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySubclass){
								$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-subclass-translate 500ms ease-out 0s normal both'});
							}
							else if(isString(options.classname) && options.classname === CSS_PREFIX+current_settings.keySuperclass){
								$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-superclass-translate 500ms ease-out 0s normal both'});
							}
							setTimeout(function(){
								runSearch(data.id);
							},500);
						}else{
							if(click_timeoutID){
//								console.log('clearTimeout');
								clearTimeout(click_timeoutID);
							}
							click_timeoutID = setTimeout(function(){
								click_timeoutID = null;
								runSearch(data.id);
							},100);
						}
						return false;
					})
					.appendTo($a_base);

					$('<span>').text(text).appendTo($a);


////					if($number_html) $number_html.appendTo($link_base);
//					if($number_html) $number_html.appendTo($a);


					//subclass
					if(isString(options.classname) && options.classname === CSS_PREFIX+current_settings.keySuperclass){
						if($number_html) $number_html.appendTo($('<'+current_settings.nodeName+'>').css({'display':'table-cell','vertical-align':'top','text-align':'right','width':'1px'}).appendTo($link_base));
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
					var id = tokenInputItem.id;
					if(isObject(tokenInputItem) && isString(tokenInputItem.id) && current_settings.id_regexp.test(tokenInputItem.id)){
						id = RegExp.$1;
					}
					tokenInputItemsHash[id] = tokenInputItem;
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

			getTokenInputElement().off('add.tokenInput');

			var params = $button.data(OBJECT_KEY) || {};

			var new_token = {id: params.self.id, name: params.self.id+' '+params.self.name};
			if(runSearchOptions.hasJA && isString(params.self.name_ja)){
				new_token['id'] =  new_token['id'].replace(/_[a-z]+/,'') +  '_ja';
				new_token['name'] = params.self.id+' '+params.self.name_ja;
			}

			if(params.exec==='add'){
				addTokenInputItem(new_token);
//				runSearchOptions.tokenInputItems.push(new_token);

//				$button.parent(current_settings.nodeName+'.'+current_settings.cssButtonBaseClass).find('button').off('click',executionAddOrReplace).css({opacity:0.2,cursor:'default'});
			}
			else if(params.exec==='replace'){
				var $selectedToken = $('li.'+tokeninput_classes['selectedToken']+'.'+current_settings.cssTokenClass);
				var selectedToken = null;
				if($selectedToken && $selectedToken.length) selectedToken = $selectedToken.data(TOKENINPUT_ITEM_SETTINGS_KEY);
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
					tokeninput_target = $.extend(true, {},params.self);
//					runSearchOptions.tokenInputItems = [];
//					$.each(new_arr, function(){runSearchOptions.tokenInputItems.push(this);});

					removeTokenInputItems();
					$.each(new_arr, function(index){
						addTokenInputItem(this,new_index === index);
					});
				}
			}

			if(isObject(runSearchOptions)){
				if(isArray(runSearchOptions.tokenInputItems)) runSearchOptions.tokenInputItems = getTokenInputItems();
				if(isArray(runSearchOptions.tokenInputItemNodes)) runSearchOptions.tokenInputItemNodes = getTokenInputItemNodes();
			}

			changeStateAddOrReplace();
			setTimeout(function(){
				$button.get(0).focus();
			},51);
			return false;
		}

		function addExecuteButtons(data,disabled){
			if(!isBoolean(disabled)) disabled = disabled ? true : false;
//			disabled = false;

			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);

			$.each(['add','replace'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-primary').addClass(key=='add'?current_settings.cssButtonAddClass:current_settings.cssButtonReplaceClass).data(OBJECT_KEY,  $.extend(true, {},data,{'exec' : key.toLowerCase()})   ).text(current_settings.language[getCurrentLanguage()][key]).appendTo($button_base);
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

		var executionLanguage_timeoutID = null;
		function executionLanguage(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};
			runSearchOptions.hasJA = params.exec==='jpn';
			if(executionLanguage_timeoutID){
//				console.log('clearTimeout');
				clearTimeout(executionLanguage_timeoutID);
			}
			executionLanguage_timeoutID = setTimeout(function(){
				executionLanguage_timeoutID = null;
				showLoading();
				showResults();
			},100);
		}

		function addLanguageButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			$.each(['jpn','eng'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn btn-success').data(OBJECT_KEY,  $.extend(true, {},{'exec' : key.toLowerCase()})   ).text(current_settings.language[getCurrentLanguage()][key]).appendTo($button_base);
				$button.on('click',executionLanguage);
			});
			return $button_base;
		}
/*
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
				var $button = $('<button>').addClass('btn btn-primary').data(OBJECT_KEY,  $.extend(true, {},{'exec' : key.toLowerCase()})   ).text(current_settings.language[getCurrentLanguage()][key]).appendTo($button_base);
				$button.on('click',executionRevert);
			});
			return $button_base;
		}
*/
		function executionPhenoTouch(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};
			if(params.exec==='phenotouch'){

				var $inlineContent = $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer : $();
				$inlineContent.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass).hide();
				$inlineContent.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass).show();
				$inlineContent.find(current_settings.nodeName+'.'+current_settings.cssWebGLSwitchContentClass).hide();
				$(window).resize();

				if(window.__threeBitsRenderer && !__threeBitsRenderer.isLoadingObj()){
//					__threeBitsRenderer.focus(__isFirstThreeBitsRenderer);
//					__threeBitsRenderer._calcCameraPos();
//					__threeBitsRenderer._render();
//					__isFirstThreeBitsRenderer = false;
/*
					var $webgl_content_base_table = $inlineContent.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass);
					console.log('__isFirstThreeBitsRenderer',__isFirstThreeBitsRenderer, $webgl_content_base_table.is(':visible'));
					if($webgl_content_base_table.is(':visible') && __isFirstThreeBitsRenderer){
						__isFirstThreeBitsRenderer = false;
					}
*/

//					click_callback();

//					$inlineContent.find(current_settings.nodeName+'.'+current_settings.cssCheckboxGroupClass).find('input[type=checkbox]').triggerHandler('click');

				}

			}
			return;
		}

		function executionClear(){
			var $button = $(this);
			var params = $button.data(OBJECT_KEY) || {};
			if(params.exec==='clear'){
				removeTokenInputItems();
			}
			return;
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
				$('div.'+tokeninput_classes['dropdown']).css({'display':'none'});
			},100);
//			console.log('end   executionOKCancel()',getTokenInputItems(),getOriginalTokenInputItems());
			return;
		}

		function addPhenoTouchButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			var language = current_settings.language[getCurrentLanguage()];
			var key = 'phenotouch';
			var $button = $('<button>').addClass('btn').addClass('btn-success').data(OBJECT_KEY,  $.extend(true, {},{'exec' : key.toLowerCase()})   ).text(language[key] ? language[key] : key).appendTo($button_base);
			$button.on('click',executionPhenoTouch);
			return $button_base;
		}

		function addClearButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			var language = current_settings.language[getCurrentLanguage()];

				var key = 'clear';
				var $button = $('<button>').addClass('btn').addClass(key=='ok'?'btn-primary':'btn-default').data(OBJECT_KEY,  $.extend(true, {},{'exec' : key.toLowerCase()})   ).text(language[key] ? language[key] : key).appendTo($button_base);

				if(current_settings.clearButtonAlign=='right'){
					$button.css({'margin-right':'20px'});
				}
				if(current_settings.clearButtonAlign=='left'){
//					$button.css({'margin-left':'140px'});
					$button.css({'margin-left':'0px'});
				}

				$button.on('click',executionClear);

			return $button_base;
		}

		function addOKCancelButtons(){
			var $button_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonBaseClass);
			var language = current_settings.language[getCurrentLanguage()];
			$.each(['ok','cancel'], function(){
				var key = this;
				var $button = $('<button>').addClass('btn').addClass(key=='ok'?'btn-primary':'btn-default').data(OBJECT_KEY,  $.extend(true, {},{'exec' : key.toLowerCase()})   ).text(language[key] ? language[key] : key).appendTo($button_base);
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

		function getContentBaseElement() {
			return $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer.find(current_settings.nodeName+'.'+current_settings.cssInlineContentBaseClass) : $();
		}

		var __last_results = null;
		function showResults(results) {
			if(results){
				__last_results = $.extend(true, {},results);
			}else if(__last_results){
				results = $.extend(true, {},__last_results);
			}
			if(!results){
				emptyInlineContent();
				return;
			}

			var language = current_settings.language[getCurrentLanguage()];

//			console.log(tokeninput_target);
			if(!tokeninput_target){
				tokeninput_target_results = $.extend(true, {},results);
				tokeninput_target = $.extend(true, {},results[current_settings.keySelfclass][0]);
			}

			var $inlineContentBase = getContentBaseElement();
			if($inlineContentBase.length==0){
				var $inlineContent = $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer : emptyInlineContent();
				$inlineContentBase = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssInlineContentBaseClass).appendTo($inlineContent);
			}

			/////////////////////////////////////////////////////////////////////////
			// tokeninput contents
			/////////////////////////////////////////////////////////////////////////
			var $table = $inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssTokenInputContentBaseClass);
			if($table.length==0){
				$table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).addClass(current_settings.cssTokenInputContentBaseClass).appendTo($inlineContentBase);
				$table.css({
//					'margin-top':'90px',
					'border-spacing':'5px',
					'margin-top':'104px',
					'margin-left':'0',
					'margin-right':'0',
					'margin-bottom':'15px'
				});

				var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).css({'width':'8.5%'}).appendTo($tr);
				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).css({'width':'83%'}).appendTo($tr);

				var $selectedphenotype_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssSelectedPhenotypeClass).css({'width':'100%'}).appendTo($td);

				var $selectedphenotype_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).appendTo($selectedphenotype_base);
				$selectedphenotype_title.empty();
				var $selectedphenotype_title_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','empty-cells':'hide','width':'100%'}).appendTo($selectedphenotype_title);
				var $selectedphenotype_title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($selectedphenotype_title_table);

				var $selectedphenotype_title_td_left = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left'}).appendTo($selectedphenotype_title_tr);

				var $selectedphenotype_title_td_center = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'center','width':'100%'}).appendTo($selectedphenotype_title_tr);
				$selectedphenotype_title_td_center.attr({'data-language-key':'selectedphenotype'}).text(language['selectedphenotype']);

				var $selectedphenotype_title_td_right = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','padding-right':'8px','position':'relative'}).appendTo($selectedphenotype_title_tr);

				var $language_button = $('<button>')
					.addClass(current_settings.cssLanguageChangeClass)
//					.css({
//						'position':'absolute',
//						'width':'70px',
//						'border':'2px solid white',
//						'top':'-2px'
//					})
					.addClass('btn btn-default')
					.appendTo($selectedphenotype_title_td_right)
					.text('')
					.click(function(e){
						e.preventDefault();
						e.stopPropagation();
						return false;
					});

				var $language_select = $('<select>')
					.attr({'name':'language'})
//					.css({
//						'opacity':'0',
//					})
					.addClass(current_settings.cssLanguageChangeClass)
					.appendTo($selectedphenotype_title_td_right)
					.change(function(){
	//					console.log('change');
						var $select = $(this);
						var $select_option = $select.find('option:selected');
	//					console.log($select_option,$select_option.val());
	//					$select_option.val()
//						$select.attr('data-language', $select_option.val());

//						console.log($select_option.text());
						$select.prev('button').html($select_option.text()+'&nbsp;▼');


						runSearchOptions.hasJA = $select_option.val()==='ja';
						if(executionLanguage_timeoutID){
			//				console.log('clearTimeout');
							clearTimeout(executionLanguage_timeoutID);
						}
						executionLanguage_timeoutID = setTimeout(function(){
							executionLanguage_timeoutID = null;
							showLoading();
							showResults();
						},100);

					});
				var $language_option_en = $('<option>').attr({'data-language-key':'eng','name':'en'}).val('en').text(language['eng']).appendTo($language_select);
				var $language_option_jp = $('<option>').attr({'data-language-key':'jpn','name':'ja'}).val('ja').text(language['jpn']).appendTo($language_select);


				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).css({'width':'8.5%'}).appendTo($tr);
//				addPhenoTouchButtons().css({'width':'100%'}).appendTo($td);
				$('<'+current_settings.nodeName+'>')
					.addClass(current_settings.cssWebGLSwitchContentClass)
					.appendTo($td)
					.data(OBJECT_KEY, $.extend(true, {},{'exec' : 'phenotouch'}) )
					.click(executionPhenoTouch);

/*
				$('<img>')
					.attr({'src':'static/css/popup-hierarchy-hpo/ICON_PhenoTouch.png','width':'100','height':'100'})
					.css({
						'width':'104px',
						'height':'104px',
						'border-radius':'10px',
						'cursor':'pointer',
						'border':'6px solid #4472C4',
						'margin-left':'15px'
					})
					.appendTo($td)
					.data(OBJECT_KEY, $.extend(true, {},{'exec' : 'phenotouch'}) )
					.click(executionPhenoTouch);
*/

				var onResult = function(results){
					getTokenInputElement().off('add.tokenInput').on('add.tokenInput', function(token){
						var $li = _addTokenInputItem(token,true);
						changeStateAddOrReplace();
						$li.trigger('click');
					});

					return results;
				};


				var $selectedphenotype_textarea = $('<'+current_settings.inputNodeName+'>').attr({'id':current_settings.inputId}).appendTo($selectedphenotype_base);
				$selectedphenotype_textarea.tokenInput(tokeninput_settings.url, $.extend(true, {}, tokeninput_settings, {zindex: 1444,
					onResult: onResult,
					onCachedResult: onResult,
					onAdd: function(token){
						getTokenInputElement().trigger('add.tokenInput',[token]);
						getTokenInputElement().trigger('add.tokenInput2',[token]);
					},
					onFreeTaggingAdd: function(token){
					},
					onDelete: function(token){
						if(isObject(runSearchOptions)){
							if(isArray(runSearchOptions.tokenInputItems)) runSearchOptions.tokenInputItems = $.grep(runSearchOptions.tokenInputItems || [],function(data){return token.id!==data.id;});
							if(isArray(runSearchOptions.tokenInputItemNodes)) runSearchOptions.tokenInputItemNodes = getTokenInputItemNodes();
						}
						changeStateAddOrReplace();
						getTokenInputElement().trigger('delete.tokenInput2',[token]);
					},
					onReady: function(){
						var $ul = $(current_settings.nodeName+'.'+current_settings.cssSelectedPhenotypeClass+ ' ul.'+tokeninput_classes['tokenList']).addClass(current_settings.cssTokenListClass);
						$ul.on('mousedown', function(e){
							var $li_node;
							if($(e.target).get(0).nodeName.toLowerCase()==='li'){
								$li_node = $(e.target);
							}
							else if($(e.target).get(0).nodeName.toLowerCase()==='p'){
								$li_node = $(e.target).parent('li');
							}
							else if($(e.target).get(0).nodeName.toLowerCase()==='span'){
								$li_node = $(e.target).parent('li');
							}
							if($li_node && $li_node.hasClass(current_settings.cssTokenClass)){
							}
							else{
								clearSelectedTokenInputItems();
								if(isObject(runSearchOptions)){
									if(isArray(runSearchOptions.tokenInputItems)) runSearchOptions.tokenInputItems = getTokenInputItems();
									if(isArray(runSearchOptions.tokenInputItemNodes)) runSearchOptions.tokenInputItemNodes = getTokenInputItemNodes();
								}
								changeStateAddOrReplace();
							}
						}).on('keydown', function(e){
							e.stopPropagation();
						});
					}
				}));


				if(runSearchOptions.tokenInputItems && runSearchOptions.tokenInputItems.length){
					runSearchOptions.tokenInputItems.forEach(function(tokenInputItem,index){
	//					console.log($selectedphenotype_textarea.tokenInput('add', tokenInputItem));
						var selectedToken = isArray(runSearchOptions.tokenInputItemNodes) && $(runSearchOptions.tokenInputItemNodes).eq(index).hasClass(tokeninput_classes['selectedToken']) ? true : false;
						addTokenInputItem(tokenInputItem,selectedToken);
					});
				}



				var $selectedphenotype_bottom_bar = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBottomBarClass).appendTo($selectedphenotype_base);
				$selectedphenotype_bottom_bar.empty();

				var $selectedphenotype_bottom_bar_table = $('<'+current_settings.nodeName+'>').css({'display':'table','border-collapse':'collapse','empty-cells':'hide','width':'100%'}).appendTo($selectedphenotype_bottom_bar);
				var $selectedphenotype_bottom_bar_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($selectedphenotype_bottom_bar_table);

				var $selectedphenotype_bottom_bar_td_left = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'4px'}).appendTo($selectedphenotype_bottom_bar_tr);
				var $selectedphenotype_bottom_bar_td_center = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'center'}).appendTo($selectedphenotype_bottom_bar_tr);
	//			addLanguageButtons().appendTo($selectedphenotype_bottom_bar_td_center);
	//			addOKCancelButtons().appendTo($selectedphenotype_bottom_bar_td_center);
				var $selectedphenotype_bottom_bar_td_right = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','padding-right':'4px'}).appendTo($selectedphenotype_bottom_bar_tr);

//				addPhenoTouchButtons().appendTo($selectedphenotype_bottom_bar_td_left);

				if(current_settings.clearButtonAlign=='left'){
					addClearButtons().appendTo($selectedphenotype_bottom_bar_td_left);
				}
				else if(current_settings.clearButtonAlign=='center'){
					addClearButtons().appendTo($selectedphenotype_bottom_bar_td_center);
				}
				else{
					addClearButtons().appendTo($selectedphenotype_bottom_bar_td_right);
				}


				if(current_settings.okcancelButtonsAlign=='left'){
					addOKCancelButtons().appendTo($selectedphenotype_bottom_bar_td_left);
				}
				else if(current_settings.okcancelButtonsAlign=='center'){
					addOKCancelButtons().appendTo($selectedphenotype_bottom_bar_td_center);
				}
				else{
					addOKCancelButtons().appendTo($selectedphenotype_bottom_bar_td_right);
				}
			}


			var $language_select = $('select[name=language]');
			$language_select.find('option').prop('selected', false);
//			$language_select.find('option[name='+getCurrentLanguage()+']').prop('selected', true);
			$language_select.prev('button').html($language_select.find('option[name='+getCurrentLanguage()+']').prop('selected', true).text()+'&nbsp;▼');

			$('*[data-language-key]').each(function(){
				var key = $(this).attr('data-language-key');
				$(this).text(language[key]);
			});


//			var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);







			/////////////////////////////////////////////////////////////////////////
			// class contents
			/////////////////////////////////////////////////////////////////////////
			$table = $inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass);
			if($table.length){
				$table.empty();
			}
			else{
				$table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).addClass(current_settings.cssClassContentBaseClass).appendTo($inlineContentBase);
			}
			var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);

			// super class content
			createOtherContent(results[current_settings.keySuperclass],{
				title: language.superclass,
				classname: CSS_PREFIX+current_settings.keySuperclass,
				formatNumber: true
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
				if(!isArray(results[current_settings.keySuperclass]) || results[current_settings.keySuperclass].length===0){
					target_arr.push('dummy');
				}

				var data = {
					'target' : $.extend(true, {},tokeninput_target),
					'self' : $.extend(true, {},results[current_settings.keySelfclass][0])
				};

				var $buttons = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssButtonsClass).appendTo($base);
				addExecuteButtons(data,target_arr.length!==0).appendTo($buttons);

				var $content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).appendTo($base);
				var $contentTable = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentTableClass).appendTo($content);

				var title_text_arr = [];

//				var language = current_settings.language[getCurrentLanguage()];

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

//						addLanguageButtons().appendTo($title_td2);

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

							var $a = $('<a>')
							.addClass(current_settings.cssLinkClass)
//							.text(value)
							.attr({'href':'#'})
							.data(OBJECT_KEY, result)
							.css({'display':'inline-block'/*,'width':'100%'*/})
							.click(function(){
								var data = $(this).data(OBJECT_KEY);
								setTimeout(function(){
									runSearch(data.id);
								},0);
								return false;
							})
							.appendTo($value_td);
							$('<span>').text(value).appendTo($a);

						}
						else{
							$value_td.text(value);
						}
					});
				});
			}

			// sub class content
			createOtherContent(results[current_settings.keySubclass],{
				title: language.subclass,
				classname:CSS_PREFIX+current_settings.keySubclass,
				formatNumber: true
			}).appendTo($tr);

			changeStateAddOrReplace();

			/////////////////////////////////////////////////////////////////////////
			// WebGL
			/////////////////////////////////////////////////////////////////////////
//			$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass).hide();	//DEBUG


			$webgl_content_base_table = $inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass);
			if($webgl_content_base_table.length==0){
				__isFirstThreeBitsRenderer = true;


				$webgl_content_base_table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).addClass(current_settings.cssWebGLContentBaseClass).appendTo($inlineContentBase);
				$webgl_content_base_table.css({'width':'84%'});
				$webgl_content_base_table.hide();

				var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($webgl_content_base_table);
				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
				$td.css({'width':'65%'});

				var $webgl_content_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssWebGLContentClass).appendTo($td);
				$webgl_content_base.css({'position':'relative'});


				var $webgl_content_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).css({'display':'table','border-collapse':'collapse','width':'100%'}).appendTo($webgl_content_base);
				var $webgl_content_title_tr = $('<'+current_settings.nodeName+'>').css({'display':'table-row'}).appendTo($webgl_content_title);
				var $webgl_content_title_td1 = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'left','padding-left':'0.5em'}).attr({'data-language-key':'webgltitle'}).text(language['webgltitle']).appendTo($webgl_content_title_tr);
				var $webgl_content_title_td2 = $('<'+current_settings.nodeName+'>').css({'display':'table-cell','text-align':'right','width':'20px'}).appendTo($webgl_content_title_tr);

//				$('<'+current_settings.nodeName+'>').addClass(current_settings.cssCloseButtonClass).text('X').click(function(){
				$('<button>')
					.addClass('btn btn-default')
					.attr({'data-language-key':'close'})
					.css({'min-width':'70px','padding':'1px 4px','border':'2px solid white'})
					.text(language['close'])
					.click(function(){
						var $inlineContentBase = getContentBaseElement();
						if($inlineContentBase.length){
							$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass).show();
							$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass).hide();
							$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssWebGLSwitchContentClass).show();
						}
					})
					.appendTo($webgl_content_title_td2);

				var $webgl_chechkbox_group = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).addClass(current_settings.cssCheckboxGroupClass).appendTo($webgl_content_base);
				$webgl_chechkbox_group.css({'height':'30px','border-bottom':'1px solid gray','padding':'2px 0px','text-align':'left','vertical-align':'middle'});

//				$.each(['bone','muscle','vessel','internal','other'], function(){
				$.each(current_settings.use_segments, function(){
					var text = this.toString();
					var name = text.toLowerCase();
					if(isString(language[name])) text = language[name];
					var id = CSS_PREFIX+'checkbox-'+name;
//					console.log(id,text,text==='Bone');
//					$('<input type=checkbox>').attr({'name':name,'value':name,'id':id}).prop('checked', name==='bone').css({'margin-left':'10px'}).appendTo($webgl_chechkbox_group);
					$('<input type=checkbox>').attr({'name':name,'value':name,'id':id}).prop('checked', name===current_settings.use_segments[0]).css({'margin-left':'10px'}).appendTo($webgl_chechkbox_group);
					$('<label>').attr({'for':id}).css({'margin-left':'2px','margin-right':'10px'}).text(text).appendTo($webgl_chechkbox_group);
				});



				var $webgl_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).appendTo($webgl_content_base);
				$webgl_content.css({'padding':'0px','position':'relative','overflow':'hidden'});

				var $webgl_home_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssWebGLHomeContentClass).appendTo($webgl_content).click(function(){
					__threeBitsRenderer._setHorizontal(0)._setVertical(0).focus(true);
					$(this).hide();
				}).hide();

				if(window.threeBitsRenderer){

//					var skin_art_ids = [];

					var _click_callback = function(use_load){
//						console.log('call _click_callback');
						if(!isBoolean(use_load)) use_load = true;

						__threeBitsRenderer.removeAllSpeechBalloon();

						var paths = [];
						var checked_category = {};
						var $checked = $webgl_chechkbox_group.find('input[type=checkbox]:checked');
//						console.log($checked);
						if($checked.length){

							var $fmalist_content_base = $(current_settings.nodeName+'.'+current_settings.cssFMAListContentClass);
							var $fmalist_content = $fmalist_content_base.find(current_settings.nodeName+'.'+current_settings.cssContentClass);
							var $fmalist_content_tr = $fmalist_content.find('table tr');
							var pick_objid_hash = {};
//							var speech_balloon_hash = {};
							var obj_color_hash = {};
							var obj_hide_hash = {};
							var fma_hide_hash = {};
							if($fmalist_content_tr.length>1){
//								console.log($fmalist_content_tr.length);
								$fmalist_content_tr.each(function(){
									var $tr = $(this);
									var fma_id = $tr.data('fma_id');
									if(isEmpty(fma_id)) return;
/*
									var $input_color = $tr.find('input[type=color][name=color]');
									if($input_color.length){
										var fma_color = $input_color.data('fma_color');
										var val_color = $input_color.val();
										if(isString(fma_color) && isString(val_color) && fma_color.toUpperCase() != val_color.toUpperCase()){
											Object.keys(fma2obj[fma_id]).forEach(function(objid){
												obj_color_hash[objid] = val_color.toUpperCase();
											});
										}
									}

									var $input_hide = $tr.find('input[type=checkbox][name=hide]:checked');
									if($input_hide.length){
										Object.keys(fma2obj[fma_id]).forEach(function(objid){
											obj_hide_hash[objid] = true;
										});
										fma_hide_hash[fma_id] = true;
									}
*/

									var fma_name = $tr.data('fma_name');
//									speech_balloon_hash[fma_id] = {text:fma_name,point:[]};

									var hash = $tr.data('pick_objid') || {};
									Object.keys(hash).forEach(function(objid){
										pick_objid_hash[objid] = hash[objid];

//										if(hash[objid].point) speech_balloon_hash[fma_id].point.push(hash[objid].point);

									});

//									if(speech_balloon_hash[fma_id].point.length==0) delete speech_balloon_hash[fma_id];


								});

/*
//								var speech_balloon_colors = ['#FF0000','#FFFF00','#00FF00','#00FFFF','#0000FF','#FF00FF','#800000','#808000','#008000','#008080','#000080','#800080'];
								var speech_balloon_colors = ['#FF0000','#00FF00','#00FFFF','#0000FF','#FF00FF','#800000','#808000','#008000','#008080','#000080','#800080'];
								var speech_balloon_colors_length = speech_balloon_colors.length;
								var speech_balloon_sort = function(a,b){
									if(speech_balloon_hash[a]['text']<speech_balloon_hash[b]['text']) return -1;
									if(speech_balloon_hash[a]['text']>speech_balloon_hash[b]['text']) return  1;
									return 0;
								};
								Object.keys(speech_balloon_hash).sort(speech_balloon_sort).forEach(function(fma_id,index){
									var color = speech_balloon_colors[(speech_balloon_colors_length+index)%speech_balloon_colors_length];
									var element = __threeBitsRenderer.createSpeechBalloon(speech_balloon_hash[fma_id].point,{text:speech_balloon_hash[fma_id].text,color:color});
								});
*/
							}
//							console.log(pick_objid_hash);

							$checked.each(function(){
								var category = $(this).val();
								checked_category[category] = null;
								if(category2obj['category'][category]){
									Object.keys(category2obj['category'][category]).forEach(function(objid){
										var params = {};
										params[Ag.Def.OBJ_ID_DATA_FIELD_ID] = objid;
										params[Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID] = isDefined(pick_objid_hash[objid]) ? '#FF0000' : (isDefined(obj_color_hash[objid]) ? obj_color_hash[objid] : category2obj['category'][category][objid][Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID]);
										params[Ag.Def.OBJ_URL_DATA_FIELD_ID] = current_settings.obj_url+objid+current_settings.obj_ext;
										params[Ag.Def.CONCEPT_DATA_OPACITY_DATA_FIELD_ID] = category=='other'?SKIN.OPACITY:1.0;
										params[Ag.Def.CONCEPT_DATA_VISIBLE_DATA_FIELD_ID] = isDefined(obj_hide_hash[objid]) ? false : true;
										params[Ag.Def.USE_FOR_BOUNDING_BOX_FIELD_ID] = false;
										params[Ag.Def.CONCEPT_DATA_SELECTED_DATA_FIELD_ID] = category=='other'?true:false;
										paths.push(params);
									});
								}
							});
						}
						if(!isDefined(checked_category['other'])){
							var category = 'other';
							if(category2obj['category'][category]){
								Object.keys(category2obj['category'][category]).forEach(function(objid){
									var params = {};
									params[Ag.Def.OBJ_ID_DATA_FIELD_ID] = objid;
									params[Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID] = category2obj['category'][category][objid][Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID];
									params[Ag.Def.OBJ_URL_DATA_FIELD_ID] = current_settings.obj_url+objid+current_settings.obj_ext;
									params[Ag.Def.CONCEPT_DATA_OPACITY_DATA_FIELD_ID] = SKIN.DEFAULT_OPACITY;
									params[Ag.Def.CONCEPT_DATA_VISIBLE_DATA_FIELD_ID] = true;
									params[Ag.Def.USE_FOR_BOUNDING_BOX_FIELD_ID] = false;
									paths.push(params);
								});
							}
						}
						if(paths.length){
							if(use_load){
								__threeBitsRenderer.loadObj(paths);
							}
							else{
								__threeBitsRenderer.setObjProperties(paths);
							}
						}
					};

					var click_callback = function(e){
//						console.log('call click_callback');
						$(__threeBitsRenderer.domElement()).one('hide', _click_callback);
						__threeBitsRenderer.hideAllObj();
					};
					$webgl_chechkbox_group.find('input[type=checkbox]').on('click', function(e){
//						console.log('click checkbox');
						__threeBitsRenderer.fireEvent('progress',__threeBitsRenderer,'Please wait...');
						setTimeout(click_callback.call(undefined,e),250)
					});



					if(!window.__threeBitsRenderer){
						window.__threeBitsRenderer = new threeBitsRenderer({
							width:108,
							height:108,
							rate:1,
							minZoom: 1,
							maxZoom: 23,
							backgroundColor: '#FFFFFF',
						});
					}
					var $domElement = $(__threeBitsRenderer.domElement());
					$domElement.show();
//					__threeBitsRenderer.domElement().style.display = '';
//					__threeBitsRenderer.hideAllObj();
					$domElement.css({'z-index':'1'}).appendTo($webgl_content)
					.on('pick', function(e,ren,intersects){
//						console.log('pick',ren,intersects,e);
//						_click_callback(false);
						var fma_ids = {};
						var fma_colors = {};
//						var hpo_ids = {};
						var fma2pickobj = {};

						var name_key = 'name';
						if(runSearchOptions.hasJA) name_key += '_ja';

						if(isArray(intersects) && intersects.length && isObject(window.category2obj)){
//							var paths_hash = {};

							var checked_category = {};
							var $checked_category = $webgl_chechkbox_group.find('input[type=checkbox]:checked');
							$checked_category.each(function(){
								var category = $(this).val();
								checked_category[category] = null;
							});



							var exists_parts = false;

							intersects.forEach(function(intersect){
								if(exists_parts) return false;
								if(isObject(intersect) && intersect.object && isString(intersect.object[Ag.Def.OBJ_ID_DATA_FIELD_ID]) && intersect.object[Ag.Def.OBJ_ID_DATA_FIELD_ID].length){
//									console.log(intersect);

									var art_id = intersect.object[Ag.Def.OBJ_ID_DATA_FIELD_ID];
//									console.log('pick','art_id',art_id);

//									Object.keys(category2obj).forEach(function(category){
									$checked_category.each(function(){
										var category = $(this).val();

										if(exists_parts) return false;
										if(isObject(category2obj['category'][category][art_id])){
//											console.log(category2obj['category'][category][art_id]);

											var color = category2obj['category'][category][art_id]['color'];

											if(isString(category2obj['category'][category][art_id]['FMA'])){
												var fma_id = category2obj['category'][category][art_id]['FMA'];


													if(exists_parts) return false;

//													if(!category2obj['category'][category][art_id]['FMA'][fma_id]['is_element']) return;
													exists_parts = true;
//													console.log('pick',category,art_id,fma_id);

													fma_ids[fma_id] = category2obj['FMA'][fma_id];
													fma_colors[fma_id] = color;

													var disp_fma_id = fma_id;
													if(fma_id.match(/^(FMA)([0-9]+.*)$/)){
														disp_fma_id = RegExp.$1+':'+RegExp.$2;
													}
													var fma_name = isString(fma_ids[fma_id][name_key]) ? fma_ids[fma_id][name_key] : fma_ids[fma_id]['name'];

													if(isEmpty(fma2pickobj[fma_id])) fma2pickobj[fma_id] = {};
													if(isEmpty(fma2pickobj[fma_id][art_id])){
														fma2pickobj[fma_id][art_id] = {
															fma_id: disp_fma_id,
															fma_name: fma_name,
															distance: intersect.distance,
															point: {
																x: intersect.point.x,
																y: intersect.point.y,
																z: intersect.point.z
															}
														};

														//該当するFMAに対応するOBJを選択状態する為
														if(exists_parts){
															if(isArray(fma_ids[fma_id]['other_art_ids'])){
																fma_ids[fma_id]['other_art_ids'].forEach(function(other_art_id){
																	fma2pickobj[fma_id][other_art_id] = {
																		fma_id: disp_fma_id,
																		fma_name: fma_name
																	};
																});
															}
															if(isObject(fma_ids[fma_id]['art_ids'])){

//																var $checked_category = $webgl_chechkbox_group.find('input[type=checkbox]:checked');
																$checked_category.each(function(){
																	var checked_category = $(this).val();
//																	if(checked_category == category) return;

																	if(isArray(fma_ids[fma_id]['art_ids'][checked_category])){

																		fma_ids[fma_id]['art_ids'][checked_category].forEach(function(other_art_id){
																			if(other_art_id == art_id) return;
																			fma2pickobj[fma_id][other_art_id] = {
																				fma_id: disp_fma_id,
																				fma_name: fma_name
																			};
																		});

																	}

																});


															}
														}

													}

											}
										}
									});
								}
							});
						}
						else{
//							click_callback();
						}
//						console.log(fma_ids,hpo_ids);

						var $fmalist_content_base = $(current_settings.nodeName+'.'+current_settings.cssFMAListContentClass);
						$fmalist_content_base.hide();
						var $fmalist_title = $fmalist_content_base.find(current_settings.nodeName+'.'+current_settings.cssTopBarClass);
						var $fmalist_content = $fmalist_content_base.find(current_settings.nodeName+'.'+current_settings.cssContentClass);
						$fmalist_content.css({'height':($fmalist_content_base.innerHeight()-$fmalist_title.height())+'px','overflow':'auto','padding':'0'});
						$fmalist_content.empty();

						var $hpolist_content_base = $(current_settings.nodeName+'.'+current_settings.cssHPOListContentClass);
						var $hpolist_title = $hpolist_content_base.find(current_settings.nodeName+'.'+current_settings.cssTopBarClass).text('');
						var $hpolist_content = $hpolist_content_base.find(current_settings.nodeName+'.'+current_settings.cssContentClass);

						var height = $webgl_content_base.innerHeight();
//						$hpolist_content.css({'max-height':($hpolist_content_base.innerHeight()-$hpolist_title.height())+'px','overflow':'auto','padding':'10px'});
						$hpolist_content.css({'max-height':(height-$hpolist_title.height())+'px','overflow':'auto','padding':'10px'});
						$hpolist_content.empty();

						if(true || Object.keys(fma_ids).length){
							var table_css = {};//{'width':'100%','font-size':'0.85em'};
							var head_css = {};//{'background-color':'#DDDDDD','cursor':'default'};
							var th_css = {};//{'padding':'0 2px','border':'1px solid #F0F0F0'};
							var td_left_css = {};//$.extend({},th_css,{'text-align':'left','vertical-align':'top'});
							var td_center_css = $.extend(true, {},td_left_css,{'padding':'0','text-align':'center'});
							var td_right_css = $.extend(true, {},td_left_css,{'padding':'0','text-align':'right'});

							var $fmalist_content_table = $('<table>').css(table_css).appendTo($fmalist_content);
							var $tr = $('<tr>').appendTo($fmalist_content_table).css(head_css);
							var $th = $('<th>').text(language['fmaid']).appendTo($tr).css(th_css);
							var $th = $('<th>').text(language['fmaname']).appendTo($tr).css(th_css);
							var $th = $('<th>').text(language['#ofphenotypes']).appendTo($tr).css(th_css);
//							var $th = $('<th>').text(language['color']).appendTo($tr).css(th_css);
//							var $th = $('<th>').text(language['hide']).appendTo($tr).css(th_css);

							var $hpolist_content_table = $('<table>').css(table_css).appendTo($hpolist_content);
							var $tr = $('<tr>').appendTo($hpolist_content_table).css(head_css);
//							var $th = $('<th>').text(language['hpoid']).appendTo($tr).css(th_css);
//							var $th = $('<th>').text(language['hponame']).attr({'colspan':'2'}).appendTo($tr).css(th_css);


							var fma_sort = function(a,b){
								var name_a = isString(fma_ids[a][name_key]) ? fma_ids[a][name_key] : fma_ids[a]['name'];
								var name_b = isString(fma_ids[b][name_key]) ? fma_ids[b][name_key] : fma_ids[b]['name'];

								if(name_a<name_b) return -1;
								if(name_a>name_b) return  1;
								return 0;
							};

							Object.keys(fma_ids).sort(fma_sort).forEach(function(fma_id,index,array){
								var disp_fma_id = fma_id;
								if(fma_id.match(/^(FMA)([0-9]+.*)$/)){
									disp_fma_id = RegExp.$1+':'+RegExp.$2;
								}
								var fma_name = isString(fma_ids[fma_id][name_key]) ? fma_ids[fma_id][name_key] : fma_ids[fma_id]['name'];
								var $tr = $('<tr>').attr({'data-fmaid':fma_id}).data({'disp_fma_id':disp_fma_id,'fma_id':fma_id,'fma_name':fma_name,'pick_objid': fma2pickobj[fma_id]||{} }).data(OBJECT_KEY, fma2obj[fma_id]).appendTo($fmalist_content_table)
								.hover(
									function(){
										var $this_tr = $(this);
										$this_tr.addClass(current_settings.cssFMAListContentHoverClass);
									},
									function(){
										var $this_tr = $(this);
										$this_tr.removeClass(current_settings.cssFMAListContentHoverClass);
									}
								)
								.click(function(){
									var language = current_settings.language[getCurrentLanguage()];

									var $this_tr = $(this);
									$fmalist_content_table.find('tr.'+current_settings.cssFMAListContentSelectClass).removeClass(current_settings.cssFMAListContentSelectClass);
									$this_tr.addClass(current_settings.cssFMAListContentSelectClass);

									var disp_fma_id = $this_tr.data('disp_fma_id');
									var fma_id = $this_tr.data('fma_id');

									var name_key = 'name';
									if(runSearchOptions.hasJA) name_key += '_ja';

									var fma = category2obj['FMA'][fma_id];

									var fma_name = fma[name_key] ? fma[name_key] : fma['name']; //$this_tr.data('fma_name');
									$hpolist_title.html(disp_fma_id+'&nbsp;'+fma_name);


									$hpolist_content.empty();
									var $hpolist_content_table = $('<table>').css(table_css).appendTo($hpolist_content);
//									var $tr = $('<tr>').appendTo($hpolist_content_table).css(head_css);
//									var $th = $('<th>').text(language['hpoid']).appendTo($tr).css(th_css);
//									var $th = $('<th>').text(language['hponame']).attr({'colspan':'2'}).appendTo($tr).css(th_css);

									var hpo_sort = function(a,b){
										var hpo_ids = isObject(category2obj['HPO']) ? category2obj['HPO'] : fma_ids[fma_id]['HPO'];

										var hpo_name_a = isString(hpo_ids[a][name_key]) ? hpo_ids[a][name_key] : hpo_ids[a]['name'];
										var hpo_name_b = isString(hpo_ids[b][name_key]) ? hpo_ids[b][name_key] : hpo_ids[b]['name'];

										if(hpo_name_a<hpo_name_b) return -1;
										if(hpo_name_a>hpo_name_b) return  1;
										return 0;
									};

									var hpo_ids = isObject(fma_ids[fma_id]['HPO']) ? Object.keys(fma_ids[fma_id]['HPO']) : fma_ids[fma_id]['HPO'];

									hpo_ids.sort(hpo_sort).forEach(function(hpo_id){
										var hpo_ids = isObject(category2obj['HPO']) ? category2obj['HPO'] : fma_ids[fma_id]['HPO'];

										var hpo_name = isString(hpo_ids[hpo_id][name_key]) ? hpo_ids[hpo_id][name_key] : hpo_ids[hpo_id]['name'];

										var $tr = $('<tr>').data({'hpo_id':hpo_id}).appendTo($hpolist_content_table);

										var $td = $('<td>').css(td_center_css).css({'white-space':'nowrap'}).appendTo($tr);
										$('<button>')
											.addClass('btn btn-primary')
											.addClass(current_settings.cssButtonAddClass)
											.data(OBJECT_KEY,{self: $.extend(true, {id:hpo_id}, hpo_ids[hpo_id]), exec:'add'})/*.css({'margin':'0','padding':'0 2px','font-size':'inherit'})*/
											.attr({'data-language-key':'add'})
											.text(language['add'])
											.appendTo($td)
											.on('click',executionAddOrReplace);

										$('<button>')
											.addClass('btn btn-primary')
											.addClass(current_settings.cssButtonReplaceClass)
											.data(OBJECT_KEY,{self: $.extend(true, {id:hpo_id}, hpo_ids[hpo_id]), exec:'replace'})/*.css({'margin':'0','padding':'0 2px','font-size':'inherit'})*/
											.attr({'data-language-key':'replace'})
											.text(language['replace'])
											.appendTo($td)
											.on('click',executionAddOrReplace);


										var $td = $('<td>').css(td_right_css).appendTo($tr);
										$('<span>').addClass(current_settings.cssLinkNumberClass).text(hpo_ids[hpo_id]['count']).appendTo($td);

//										var $td = $('<td>').text(hpo_id).appendTo($tr).css(td_left_css);
										var $td = $('<td>')/*.text(hpo_name)*/.appendTo($tr).css(td_left_css);


										var $a = $('<a>')
										.addClass(current_settings.cssLinkClass)
					//					.text(text)
										.attr({'href':'#'})
										.data(OBJECT_KEY, {id:hpo_id})
										.click(function(){
											var data = $(this).data(OBJECT_KEY);

											if(false){
												if(isString(options.classname) && options.classname === CSS_PREFIX+settings.keySubclass){
													$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-subclass-translate 500ms ease-out 0s normal both'});
												}
												else if(isString(options.classname) && options.classname === CSS_PREFIX+current_settings.keySuperclass){
													$(current_settings.nodeName+'.'+current_settings.cssTableClass).css({'animation':'popup-hierarchy-hpo-keyframe-superclass-translate 500ms ease-out 0s normal both'});
												}
												setTimeout(function(){
													runSearch(data.id);
												},500);
											}else{
												if(click_timeoutID){
					//								console.log('clearTimeout');
													clearTimeout(click_timeoutID);
												}
												click_timeoutID = setTimeout(function(){
													click_timeoutID = null;
													runSearch(data.id);
												},100);
											}
											return false;
										})
										.appendTo($td);

										$('<span>').text(hpo_name).appendTo($a);



									});
									changeStateAddOrReplace();
								});
								var $td = $('<td>').text(disp_fma_id).appendTo($tr).css(td_left_css);
								var $td = $('<td>').text(fma_name).appendTo($tr).css(td_left_css);
								var $td = $('<td>').text(fma_ids[fma_id]['#HPO']).appendTo($tr).css(td_center_css);
/*
								var $td = $('<td>').appendTo($tr).css(td_center_css);
								var $input_color = $('<input type=color>').attr({name:'color'}).data({'fma_color':fma_colors[fma_id]}).val(fma_colors[fma_id]).appendTo($td)
								.on('input',function(){	//FFでは、パレットで色を選択するたびに発生する。chromeでは、changeと同じタイミングでchangeの直前に発生する
									console.log('input',$(this).val());
									var $input_color = $(this);
								})
								.on('change',function(){
									console.log('change',$(this).val());
									var $input_color = $(this);
									_click_callback(false);
								});
								$input_color.get(0).select();
//								console.log('$input_color',$input_color.val());
*/
/*
								var $td = $('<td>').appendTo($tr).css(td_center_css).click(function(e){
									var $td = $(this);
									$td.find('input[type=checkbox]').trigger('click');
									e.preventDefault();
									e.stopPropagation();
									return false;
								});
								$('<input type=checkbox>').attr({name:'hide'}).data(OBJECT_KEY, fma2obj[fma_id]).appendTo($td).click(function(e){
									_click_callback(false);
									e.stopPropagation();
								});
*/

								if(index==0){
									setTimeout(function(){
										$tr.click();
									},100);
								}

							});

						}
						_click_callback(false);

					})
					.on('rotate', function(e,ren,value){
//						console.log('rotate',ren,value);
//						console.log('rotate',value);
						if(value.H != 0 || value.V != 0){
//							$(current_settings.nodeName+'.'+current_settings.cssWebGLHomeContentClass).show();
						}
					})
					.on('zoom', function(e,ren,value){
//						console.log('zoom',ren,value);
//						console.log('zoom',value);
						if(value != 1){
//							$(current_settings.nodeName+'.'+current_settings.cssWebGLHomeContentClass).show();
						}
					})
					.on('load', function(e,ren,successful,loadedParams){
//						console.log('load',e,ren,successful,loadedParams);
						var $progressElem = $webgl_content_base.find(current_settings.nodeName+'.'+current_settings.cssProgressClass);
						$progressElem.remove();

						if(isArray(loadedParams) && loadedParams.length){
							var loadedParamsHash = {};
							loadedParams.forEach(function(loadedParam){
								if(isObject(loadedParam) && isString(loadedParam[Ag.Def.OBJ_ID_DATA_FIELD_ID]) && loadedParam[Ag.Def.OBJ_ID_DATA_FIELD_ID].length){
									loadedParamsHash[loadedParam[Ag.Def.OBJ_ID_DATA_FIELD_ID]] = true;
								}
							});

							if(isObject(window.category2obj)){
								Object.keys(category2obj['category']).forEach(function(category){
									if(isObject(category2obj['category'][category])){
										Object.keys(category2obj['category'][category]).forEach(function(objid){
											if(isBoolean(loadedParamsHash[objid]) && loadedParamsHash[objid]) category2obj['category'][category][objid]['loaded'] = true;
										});
									}
								});
							}
						}

						if(successful){
							setTimeout(function(){
								var paths = [];

								$webgl_chechkbox_group.find('input[type=checkbox]:not(:checked)').each(function(){
									var $checkbox = $(this);
									if($checkbox/* && $checkbox.val()!='other'*/){
										var category = $checkbox.val();
//										console.log(category);

										if(isObject(category2obj['category'][category])){
											Object.keys(category2obj['category'][category]).forEach(function(objid){
												if(category2obj['category'][category][objid]['loaded']) return;
												var params = {};
												params[Ag.Def.OBJ_ID_DATA_FIELD_ID] = objid;
												params[Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID] = category2obj['category'][category][objid][Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID];
												params[Ag.Def.OBJ_URL_DATA_FIELD_ID] = current_settings.obj_url+objid+current_settings.obj_ext;
												params[Ag.Def.CONCEPT_DATA_OPACITY_DATA_FIELD_ID] = 1;
												params[Ag.Def.CONCEPT_DATA_VISIBLE_DATA_FIELD_ID] = false;
												params[Ag.Def.USE_FOR_BOUNDING_BOX_FIELD_ID] = false;
												paths.push(params);
											});
										}
									}
								});
								if(paths.length) __threeBitsRenderer.loadObj(paths);
							},100);

//							console.log('__isFirstThreeBitsRenderer',__isFirstThreeBitsRenderer, $webgl_content_base_table.is(':visible'));
							if(__isFirstThreeBitsRenderer && $webgl_content_base_table.is(':visible')){
								__threeBitsRenderer.focus(__isFirstThreeBitsRenderer);
								__threeBitsRenderer._calcCameraPos();
								__threeBitsRenderer._render();
								__isFirstThreeBitsRenderer = false;
							}

						}

					})
					.on('progress', function(e,ren,message){
//						console.log('progress',e,ren,message);
						var $progressElem = $webgl_content_base.find(current_settings.nodeName+'.'+current_settings.cssProgressClass);
//						console.log('progress',$progressElem.length);
						if($progressElem.length==0){
							$progressElem = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssProgressClass).appendTo($webgl_content_base);
						}
						if(isString(message) && message.length){
							$progressElem.text(message);
							var innerHeight = $progressElem.innerHeight();
							if(innerHeight<16) innerHeight = 16;
							$progressElem.css({'line-height':innerHeight+'px'});
						}
						else{
							$progressElem.remove();
						}
					})
					;
					if(isObject(window.category2obj)){
						click_callback();
					}
				}




				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
				$td.css({'width':'35%'/*,'padding-left':'30px'*/});

				$table = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTableClass).appendTo($td);
				$table.css({'border-spacing':'0'});

				//FMA List
				var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
				var $fmalist_content_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssFMAListContentClass).appendTo($td);
				$fmalist_content_base.hide();

				var $fmalist_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).text(language['fmalisttitle']).appendTo($fmalist_content_base);
				$fmalist_title.css({'text-align':'left','padding-left':'0.5em'});
				var $fmalist_content = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssContentClass).appendTo($fmalist_content_base);

				var $fmalist_content_table = $('<table>').appendTo($fmalist_content);
				var $tr = $('<tr>').appendTo($fmalist_content_table);
				var $th = $('<th>').text(language['fmaid']).appendTo($tr);
				var $th = $('<th>').text(language['fmaname']).appendTo($tr);
				var $th = $('<th>').text(language['#ofphenotypes']).appendTo($tr);


				//HPO List
				var $tr = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTrClass).appendTo($table);
				var $td = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTdClass).appendTo($tr);
				if($fmalist_content_base.is(':visible')) $td.css({'padding-top':'20px'});

				var $hpolist_content_base = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssBaseClass).addClass(current_settings.cssHPOListContentClass).appendTo($td);
				var $hpolist_title = $('<'+current_settings.nodeName+'>').addClass(current_settings.cssTopBarClass).css({'min-height':'27px'}).text(language['hpolisttitle']).appendTo($hpolist_content_base);
				$hpolist_title.css({'text-align':'left','padding-left':'0.5em'});
				var $hpolist_content = $('<'+current_settings.nodeName+'>').css({'min-height':'27px'}).addClass(current_settings.cssContentClass).appendTo($hpolist_content_base);

				var $hpolist_content_table = $('<table>').appendTo($hpolist_content);
//				var $tr = $('<tr>').appendTo($hpolist_content_table);
//				var $th = $('<th>').text(language['hpoid']).appendTo($tr);
//				var $th = $('<th>').text(language['hponame']).attr({'colspan':'2'}).appendTo($tr);


				$(window).resize(function(){

//					var css_overflow = $($.magnificPopup.instance.contentContainer).css('overflow');
//					$($.magnificPopup.instance.contentContainer).css('overflow','hidden');
					try{
						var margin_top = Math.round($(window).innerHeight()*0.05);//0.0945;
						if(margin_top<0) margin_top = 0;
						$(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssTokenInputContentBaseClass).css({'margin-top': margin_top+'px'});
	//					console.log(margin_top);

	//					console.log($webgl_content.width(),$webgl_content.height());
						if($webgl_content_base_table.is(':visible') && $webgl_content.innerWidth()>0){
	//						$webgl_content.css({'height':$webgl_content.innerWidth() - 90});

							var webgl_content_height = $(window).innerHeight() - $webgl_content_base_table.offset().top - 120;
							if(webgl_content_height<100) webgl_content_height = 100;
							$webgl_content.css({'height': webgl_content_height });

							if(window.__threeBitsRenderer){
//								if(__webglResizeTimeoutID) clearTimeout(__webglResizeTimeoutID);
//								__webglResizeTimeoutID = setTimeout(function(){
									__webglResizeTimeoutID = null;

	//								console.log($webgl_content.innerWidth(),$webgl_content.innerHeight());
//									console.log($webgl_content.innerWidth(),$webgl_content.width(),$('.popup-hierarchy-hpo-webgl-content>.popup-hierarchy-hpo-content').width());

									__threeBitsRenderer._setSize($webgl_content.innerWidth(),$webgl_content.innerHeight());

									if(__isFirstThreeBitsRenderer && !__threeBitsRenderer.isLoadingObj() && $webgl_content_base_table.is(':visible')){
										__threeBitsRenderer.focus(__isFirstThreeBitsRenderer);
										__threeBitsRenderer._calcCameraPos();
										__isFirstThreeBitsRenderer = false;
									}
									__threeBitsRenderer._render();
//								},0);
							}

							if($fmalist_content_base.is(':visible')){
								var height = $webgl_content_base.innerHeight() / 2 - 10;
	//							$fmalist_content_base.css({'height':height});
	//							$hpolist_content_base.css({'height':height});

								$fmalist_content.css({'height':($fmalist_content_base.innerHeight()-$fmalist_title.height())+'px','overflow':'auto','padding':'0'});
								$hpolist_content.css({'max-height':($hpolist_content_base.innerHeight()-$hpolist_title.height())+'px','overflow':'auto','padding':'10px'});
							}
							else{
								var height = $webgl_content_base.innerHeight();
	//							console.log('height',height);
	//							$hpolist_content_base.css({'height':height});
	//							$hpolist_content.css({'max-height':($hpolist_content_base.innerHeight()-$hpolist_title.height())+'px','overflow':'auto','padding':'10px'});
								$hpolist_content.css({'max-height':(height-$hpolist_title.height())+'px','overflow':'auto','padding':'10px'});
							}
						}
					}catch(e){
						console.error(e);
					}
//					$($.magnificPopup.instance.contentContainer).css('overflow',css_overflow);

				});
				$webgl_content_base_table.hide();


				getTokenInputElement()
				.on('add.tokenInput2',function(){
					if($webgl_content_base_table.is(':visible')){
						setTimeout(function(){
							$(window).resize();
						},0);
					}
				})
				.on('delete.tokenInput2',function(){
					if($webgl_content_base_table.is(':visible')){
						setTimeout(function(){
							$(window).resize();
						},0);
					}
				});

			}
			else{
				$('tr.'+current_settings.cssFMAListContentSelectClass).triggerHandler('click');
			}
//			$webgl_content_base_table.hide();
			//常に切り替える場合
//			$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass).show();
//			$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass).hide();


			/////////////////////////////////////////////////////////////////////////
			// token inputのリスト用のdivを移動
			/////////////////////////////////////////////////////////////////////////
			var $tokeninput_dropdown = getInlineContent().next('div.'+tokeninput_classes['dropdown']);
			if($tokeninput_dropdown.length) $tokeninput_dropdown.appendTo($inlineContentBase);


			if($(current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.'+current_settings.cssInlineContentBaseClass).length){
				openMagnificPopup({
	//				items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.'+current_settings.cssTableClass },
					items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName + '.'+current_settings.cssInlineContentBaseClass },
	//				items: {src:   current_settings.nodeName+'.'+current_settings.cssInlineContentClass+'>'+ current_settings.nodeName },
					type: 'inline',
					modal: false,
					showCloseBtn: false
				});
			}
			else{
				getContentBaseElement().show();
				getLoadingElement().hide();

				$(document.body).off('keydown', eventKeydown);

				var timeoutID;
				var func = function(){
					if(timeoutID){
						clearTimeout(timeoutID);
						timeoutID = null;
					}
					var $a = $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer.find(current_settings.nodeName+'.'+current_settings.cssSelfContentClass+' a.'+current_settings.cssLinkClass) : $();
					if($a.length){
						$a.addClass(current_settings.cssLinkFocusClass);
						$a.get(0).focus();
						$(document.body).on('keydown', eventKeydown);
					}
					else{
						timeoutID = setTimeout(func,100);
					}
				};
				func();

				$(window).resize();

			}
		}

		function eventKeydown(e){
			//37←, 39→, 38↑, 40↓, 13:enter,
			var $a = $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer.find(current_settings.nodeName+'.'+current_settings.cssTdClass+' a.'+current_settings.cssLinkClass+'.'+current_settings.cssLinkFocusClass) : $();
			if($a.length){
				if(e.which==13){
					$a.get(0).click();
				}
				else if(e.which==38){
//					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseRowClass;
					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseClass;
					var $prev_a = $a.parents(expr).prev(expr).find('a.'+current_settings.cssLinkClass);
					if($prev_a.length){
						$a.removeClass(current_settings.cssLinkFocusClass);
						$prev_a.eq(0).addClass(current_settings.cssLinkFocusClass).get(0).focus();
						e.stopPropagation();
						e.preventDefault();
						return false;
					}
				}
				else if(e.which==40){
//					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseRowClass;
					var expr = current_settings.nodeName+'.'+current_settings.cssLinkBaseClass;
					var $next_a = $a.parents(expr).next(expr).find('a.'+current_settings.cssLinkClass);
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
//			console.log(magnificPopup);
			if(magnificPopup && isFunction(magnificPopup.close)){

				if(window.__threeBitsRenderer){
					var $domElement = $(__threeBitsRenderer.domElement());
					$domElement.off('pick').off('rotate').off('zoom').off('load').off('progress');
//					console.log($domElement.parent().get(0));
					if($domElement.parent().get(0)!=document.body){
						$domElement.appendTo(document.body);
						$domElement.hide();
//						__isFirstThreeBitsRenderer = true;
					}
					else{
//						$().appendTo($webgl_content)
					}
				}



				magnificPopup.close();
			}
		}
		var timeoutID = null;
		function openMagnificPopup(params){
			closeMagnificPopup();

			if(timeoutID){
				clearTimeout(timeoutID);
				timeoutID = null;
			}

			params = $.extend(true, {}, params, {
				enableEscapeKey: false,
				closeOnBgClick: false,
				callbacks: {
					beforeOpen: function() {
//						console.log('beforeOpen');
					},
					elementParse: function(item) {
//						console.log('elementParse');
					},
					change: function() {
//						console.log('change');
					},
					resize: function() {
//						console.log('resize');
					},
					open: function() {
						if(getLoadingElement().is(':visible')){
//							console.log('open loading!!');
							return
						}

//						console.log('open');

						var func = function(){
							if(timeoutID){
								clearTimeout(timeoutID);
								timeoutID = null;
							}
							var $a = $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer.find(current_settings.nodeName+'.'+current_settings.cssSelfContentClass+' a.'+current_settings.cssLinkClass) : $();
							if($a.length){
								$a.addClass(current_settings.cssLinkFocusClass);
								$a.get(0).focus();
								$(document.body).on('keydown', eventKeydown);
							}
							else{
								timeoutID = setTimeout(func,100);
							}
						};
						func();

					},
					beforeClose: function() {
//						console.log('beforeClose');
					},
					close: function() {
//						console.log('close');
						$(document.body).off('keydown', eventKeydown);
					},
					afterClose: function() {
//						console.log('afterClose');
					},
					updateStatus: function(data) {
//						console.log('updateStatus');
					}
				}
			});
			$.magnificPopup.open(params);
		}

		function getLoadingElement() {
			return $.magnificPopup.instance.contentContainer ? $.magnificPopup.instance.contentContainer.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssLoadingClass) : $();
		}

		function showLoading() {
			var $loadingElement = getLoadingElement();
			if($loadingElement.length){
				$loadingElement.show();
				getContentBaseElement().hide();
			}
			else{
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
			}
		}

		var runSearchOptions = {hasJA:false};
		function runSearch(query,options) {

			loadAllObj();

			if(isObject(options) && isObject(runSearchOptions)){
				if(options.tokenInputItems && runSearchOptions.tokenInputItems) delete runSearchOptions.tokenInputItems;
				if(options.tokenInputItemNodes && runSearchOptions.tokenInputItemNodes) delete runSearchOptions.tokenInputItemNodes;
			}
			if(isObject(options)){
				if(isString(options['lang'])){
					options['hasJA'] = (options['lang'].toLowerCase()==='ja' || options['lang'].toLowerCase()==='jpn') ? true : false;
					delete options['lang'];
				}
			}
			runSearchOptions = $.extend(true, {}, runSearchOptions, options || {});

			if(isString(query) && query.length){
				runSearchOptions.lastQuery = query;
			}
			else if(isString(runSearchOptions.lastQuery) && runSearchOptions.lastQuery.length){
				query = runSearchOptions.lastQuery;
			}
			else{
				query = '';
			}

			var $inlineContentBase = getContentBaseElement();
			if($inlineContentBase.length){
				$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssClassContentBaseClass).show();
				$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssTableClass+'.'+current_settings.cssWebGLContentBaseClass).hide();
				$inlineContentBase.find(current_settings.nodeName+'.'+current_settings.cssWebGLSwitchContentClass).show();
			}

			showLoading();
//			return;

			var url = computeURL();

			var cache_key = query + url;
			var cached_results = cache.get(cache_key);
			cached_results = null;
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

					if(isFunction(settings.onSend)){
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

		if (isString(url_or_data_or_function) || isFunction(url_or_data_or_function)) {
			current_settings.url = url_or_data_or_function;
			var url = computeURL();
			if (isEmpty(current_settings.crossDomain) && isString(url)) {
				if(url.indexOf("://") === -1) {
					current_settings.crossDomain = false;
				} else {
					current_settings.crossDomain = (location.href.split(/\/+/g)[1] !== url.split(/\/+/g)[1]);
				}
			}
		} else if (isObject(url_or_data_or_function)) {
			current_settings.local_data = url_or_data_or_function;
		}

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
//						click_text = $li_node.children('p').text();
						click_text = $li_node.data(TOKENINPUT_ITEM_SETTINGS_KEY).name;
					}
					else if($(this).get(0).nodeName.toLowerCase()==='p'){
						$li_node = $(this).parent('li');
//						click_text = $(this).text();
						click_text = $li_node.data(TOKENINPUT_ITEM_SETTINGS_KEY).name;
					}
					else if($(this).get(0).nodeName.toLowerCase()==='span'){
						$li_node = $(this).parent('li');
//						click_text = $li_node.children('p').text();
						click_text = $li_node.data(TOKENINPUT_ITEM_SETTINGS_KEY).name;
					}

					var tokenInputItems;
					var tokenInputItemNodes;
					var tokenInputItem;
					var options = {};

//					if($li_node){
//						console.log($li_node.hasClass(current_settings.cssTokenClass));
//					}
					if($li_node){
						if($li_node.hasClass(current_settings.cssTokenClass)){
							tokenInputItems = getTokenInputItems();
							tokenInputItemNodes = getTokenInputItemNodes();
							tokenInputItem = getTokenInputItemFromName(click_text);
						}
						else{
							tokenInputItems = getOriginalTokenInputItems();
							tokenInputItemNodes = getOriginalTokenInputItemNodes();
							tokenInputItem = getOriginalTokenInputItemFromName(click_text);
						}
						options.hasJA = hasJA(tokenInputItem.name);
						$(tokenInputItemNodes).removeClass(tokeninput_classes['selectedToken']);
						$li_node.addClass(tokeninput_classes['selectedToken']);
					}

//					var tokenInputItem = getTokenInputItemFromName(click_text);
					if(tokenInputItem){
						tokeninput_target = null;
						tokeninput_target_results = null;
//						var options = {
//							hasJA: hasJA(tokenInputItem.name)
//						};
						if(tokenInputItems) options.tokenInputItems = tokenInputItems;
						if(tokenInputItemNodes) options.tokenInputItemNodes = tokenInputItemNodes;
						runSearch(tokenInputItem.id,options);
					}
					else{
//						console.warn(click_text,tokeninput_array);
					}
					return false;
				});


			}
		}

/*
*/
		var fma2obj = {};
		var execLoadAllObjFlag = false;
		function loadAllObj(){

			if(execLoadAllObjFlag) return;
			execLoadAllObjFlag=true;

			if(isObject(window.category2obj)){
				var paths = [];
//				Object.keys(category2obj).forEach(function(category){
				current_settings.use_segments.forEach(function(category){
					if(isObject(category2obj['category'][category])){
						Object.keys(category2obj['category'][category]).forEach(function(objid){
							var params = {};
							params[Ag.Def.OBJ_ID_DATA_FIELD_ID] = objid;
							params[Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID] = category2obj['category'][category][objid][Ag.Def.CONCEPT_DATA_COLOR_DATA_FIELD_ID];
							params[Ag.Def.OBJ_URL_DATA_FIELD_ID] = current_settings.obj_url+objid+current_settings.obj_ext;
							params[Ag.Def.CONCEPT_DATA_OPACITY_DATA_FIELD_ID] = 1;
							params[Ag.Def.CONCEPT_DATA_VISIBLE_DATA_FIELD_ID] = false;
							params[Ag.Def.USE_FOR_BOUNDING_BOX_FIELD_ID] = false;
							paths.push(params);

							Object.keys(category2obj['category'][category][objid]['FMA']).forEach(function(fma_id){
								fma2obj[fma_id] = fma2obj[fma_id] || {};
								fma2obj[fma_id][objid] = category;//category2obj['category'][category][objid];
							});

						});
					}
				});

//				console.log(fma2obj);
//				console.log(paths.length);
				if(paths.length){

					if(window.threeBitsRenderer){
						if(!window.__threeBitsRenderer){
							window.__threeBitsRenderer = new threeBitsRenderer({
								width:108,
								height:108,
								rate:1,
								minZoom: 1,
								maxZoom: 23,
								backgroundColor: '#FFFFFF',
							});
							var $domElement = $(__threeBitsRenderer.domElement());
							$domElement.appendTo(document.body);
							$domElement.hide();
						}
						__threeBitsRenderer.loadObj(paths);
//						console.log('__threeBitsRenderer.loadObj(paths);');
					}
					else{
					}
				}
			}
		}
//		loadAllObj();



		$.PopupRelationHPO = function(query,options){
			var tokenInputItems = getOriginalTokenInputItems();
			var tokenInputItemNodes = getOriginalTokenInputItemNodes();

			options = options || {}
			if(isEmpty(options['lang'])) options['lang'] = window.navigator.language.indexOf('ja')===0 ? 'ja' : 'en';

			var o = $.extend(true, {}, options || {});
			if(tokenInputItems) o.tokenInputItems = tokenInputItems;
			if(tokenInputItemNodes) o.tokenInputItemNodes = tokenInputItemNodes;

			if(isEmpty(query)) query = current_settings.defaultTokenId;// 'HP:0000118';

			runSearch(query,o);
		}
	};

}(jQuery));

$(document).ready(_onload());

const SERVER_POST_URL = "https://pubcasefinder.dbcls.jp/get_hpo_by_text";
const SERVER_POST_LIMIT = 30;
const HPO_DIC = "/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.withengkey.v7.tsv";

function _onload() {

    //activate tool-tip
    $('[data-toggle="tooltip"]').tooltip();

    //paste sample text
    $("#btn_paste_sampletext").click(function (){
        let example = "【全体像(1)】コントロール不良の高血圧(Hypertension)・糖尿病(Diabetes mellitus)で定期通院中の82歳女性の尿蛋白・全身浮腫。"+
                      "ネフローゼ症候群を中心とした腎疾患を疑い，腎生検を含めた精査目的での入院。<br>"+
                      "【主訴】全身倦怠感，全身浮腫<br>【現病歴(2)】入院1か月前より倦怠感が出現し徐々に増悪，"+
                      "2週間前に足のむくみに気付き，1週間前にはいつもの靴が履けなくなり前医受診。"+
                      "ネフローゼ症候群疑いで○月○日当院紹介入院となった。週単位で増悪傾向の浮腫あり。圧"+
                      "痕性浮腫で，下肢に目立つが面・上肢にも見られ全身性。靴下の跡がつくがすぐに消える。"+
                      "皮膚の熱感や疼痛の自覚なし。心不全症状：なし。肝不全症状：なし。先行感染症状：なし<br>"+
                      "【既往歴(3)】高血圧症（20年前に指摘され内服治療中，普段は150/80 mmHg前後），"+
                      "糖尿病（15年前に指摘され内服治療中，普段はHbA1c 8％前後），急性腎盂腎炎（5年前），"+
                      "急性虫垂炎（65年前に虫垂切除術）。輸血歴なし，アレルギー歴なし，妊娠歴：3妊２産１流。";
        example=example.replace(/<br>/g,'\n');
        $("#textarea_userinput").val(example);
        return false;
    });

    $("#btn_parse_userinput").on("click", function() {

        _initialize();

        let note = $("#textarea_userinput").val().trim();
        note.replace(/(?:\r\n|\r)/g, '\n');
        if(note.length === 0) {
            alert('患者の症状または診療録を入力してください!');
            $("#textarea_userinput").focus();
            return false;
        }  

        let hpo_dic = _get_HPO_DIC();
        if(hpo_dic.length === 0) {
            // load json from server
            if(_load_HPO_DIC_from_server(_parse_text,note) === false){
                return;
            }
        }else {
            _parse_text(note);
        }
    });


    $("#p_parsed_text").on("mouseup", function(event) {

        _clear_match_chosen_status();
        
        _hidePopup();

        let offsetEl = document.getElementById("p_parsed_text");
        let range = _getSelectionCharOffsetsWithin(offsetEl);
        let str = $.trim(range.text);
        if(str.length > 0){

           $("#ul_popup").find("li").remove();
           let li_str = "";
           let matches_list = _get_matches();
           let overlap_list = _find_overlap(range.start,range.end,matches_list);
           if(overlap_list.length > 0){
               _choose_match_from_textarea(overlap_list[0]);
               li_str = '<li><a onClick=\"_load_match_from_server('+range.start +','+range.end+');\">アノテーションを変更</a></li>';
               li_str = li_str + '<li><a onClick=\"_modify_matchrange_from_selectedtext('+range.start +','+range.end+');\">アノテーション領域を変更</a></li>';    
           }else {
               li_str = '<li><a onClick=\"_load_match_from_server('+range.start +','+range.end+');\">アノテーションを追加</a></li>';
           }
           $('#ul_popup').append(li_str);

           let offset, _ref1;
           if ((_ref1 = $(offsetEl).css("position")) !== "absolute" && _ref1 !== "fixed" && _ref1 !== "relative") {
               offsetEl = $(offsetEl).offsetParent()[0];
           }
           offset = $(offsetEl).offset();

           $("#div_selectionPopup").css("display","block");
           $("#div_selectionPopup").css("top",event.pageY - offset.top);
           $("#div_selectionPopup").css("left",event.pageX - offset.left);
        } else{
           $("#div_selectionPopup").css("display","none");
        }
    });


    $("#btn_save_annotation").on("click", function() {
        let original_text = $("#textarea_userinput").val().trim();
        let normalized_text = _get_normalized_text();
        let matches_list = _get_matches();
        
        let obj = {original_text:   original_text,
                   normalized_text: normalized_text,
                   matches_list:    matches_list
        };
        let content = JSON.stringify(obj);

        let format_str = _getTimeStamp();
        let filename = "Text2Hpo_result-"+ format_str + ".json";

        _save_text(filename,content);
    });

    $("#input_file_annotation").on('change', function() {    
        let file = document.getElementById('input_file_annotation').files[0];
        if(!window.FileReader){
            alert("File APIに対応したブラウザでご確認ください");
            return;
        }

        if(file !== undefined) {
            let reader = new FileReader();
            reader.readAsText(file, 'UTF-8');
            reader.onload = function(evt) {
                let input_json;
                try {
                     input_json = JSON.parse(evt.target.result);
                } catch (error) {
                     alert("Parse Indicated JSON file(" + file.name +") failed. " + error);
                     return;
                }

                if(input_json.hasOwnProperty("original_text") && input_json.hasOwnProperty("normalized_text") && input_json.hasOwnProperty("matches_list")){

                    _initialize();

                    let hpo_dic = _get_HPO_DIC();
                    if(hpo_dic.length === 0) {
                        if(_load_HPO_DIC_from_server() === false){
                            return;
                        }
                    }

                    let orig_text = input_json.original_text;
                    $("#textarea_userinput").val(orig_text);

                    let text = input_json.normalized_text;
                    _store_normalized_text(text);

                    let matches_lst = input_json.matches_list;
                    _store_matches(matches_lst);


                    _create_and_set_result_contents(text,matches_lst);

                    $("#div_ResultsPanel").show();
                    $("#div_outputPanel").show();
                    $('html, body').animate({scrollTop: $("#btn_parse_userinput").offset().top},100);

                } else {
                    alert("指定されたファイル [" + file.name +"]のフォーマットは間違った");
                }
            //alert(evt.target.result);
            //document.getElementById('content').innerHTML = evt.target.result;
            };
        }

        $(this).val('');
    });    

    // load HPO Dic
    //_load_HPO_DIC_from_server();
//    setTimeout(function () {
//        _load_HPO_DIC_from_server();
//    }, 500);


    document.getElementById("div_selectionPopup").onclick = function (e) {
         e = e || window.event;
            if (window.event) {
                e.cancelBubble = true;
            } else {
                e.stopPropagation();
            }
    };
    
    document.body.onclick = function (e) {
            e = e || window.event;
            var target = e.target || e.srcElement;
            if (target.id === "p_parsed_text") return;
            _hidePopup();
    };

}


function _hidePopup(){
    $("#div_selectionPopup").css("display","none");
}


function _getTimeStamp(){
        let date = new Date();
        let year_str = date.getFullYear();
        let month_str = 1 + date.getMonth();
        let day_str = date.getDate();
        let hour_str = date.getHours();
        let minute_str = date.getMinutes();
        let second_str = date.getSeconds();
        month_str = ('0' + month_str).slice(-2);
        day_str = ('0' + day_str).slice(-2); 
        hour_str = ('0' + hour_str).slice(-2);
        minute_str = ('0' + minute_str).slice(-2);
        second_str = ('0' + second_str).slice(-2);

        let format_str = 'YYYY-MM-DD-hh-mm-ss';
        format_str = format_str.replace(/YYYY/g, year_str);
        format_str = format_str.replace(/MM/g, month_str);
        format_str = format_str.replace(/DD/g, day_str);
        format_str = format_str.replace(/hh/g, hour_str);
        format_str = format_str.replace(/mm/g, minute_str);
        format_str = format_str.replace(/ss/g, second_str);

        return format_str;
}

function _tsv2JSON(tsv){

  let lines=tsv.split("\n");

  let result = [];

  let headers=lines[0].split("\t");

  for(let i=1;i<lines.length;i++){

      if(lines[i].length > 0){
          let obj = {};
          let currentline=lines[i].split("\t");

          for(let j=0;j<headers.length;j++){
              obj[headers[j]] = _normalize_text(currentline[j]);
          }

          if(obj.FLAG == 1){
              obj.SEARCH_KEY = obj.JT.toUpperCase();
          } else {
              obj.SEARCH_KEY = obj.ET.toUpperCase();
          }

          result.push(obj);
      }
  }

  //return result; //JavaScript object
  //return JSON.stringify(result); //JSON
  return result;
}

function _initialize(){

    _clear_normalized_text();

    _clear_matches();

    _clear_result_contents();

    $("#div_ResultsPanel").hide();

    $("#div_outputPanel").hide();

}

function _clear_result_contents(){
    $("#p_parsed_text").empty();

    $("#ul_matches").find("li").remove();

    $("#tbl_hpolist").find("tr:gt(0)").remove();
     
    _hidePopup();
    
    $("#btn_download").prop('disabled', true);
    
    $("#btn_save_annotation").prop('disabled', true);
}

function _set_hpo_totalnum(tbldata) {
    let total = 0;
    let with_s = 0;
    let without_s = 0;

    Object.keys(tbldata).sort().forEach(function (hpo_id) {
        total++;
        if (tbldata[hpo_id].symptoms) {
            with_s++;
        }else{
            without_s++;
        }
    });
    $('#div_total_hpo_num').text('合計 ' + total + '件(症状あり'+with_s+'件、症状なし'+without_s+'件)');
}

function _set_match_totalnum(matches_lst){

    let total = 0;
    let with_s = 0;
    let without_s = 0;

    matches_lst.forEach(function (item) {
        total++;
        if (item.with_symptoms) {
            with_s++;
        }else{
            without_s++;
        }
    });

    $('#div_total_match_num').text('合計 ' + total + '件(症状あり'+with_s+'件、症状なし'+without_s+'件)');
}


function _create_and_set_result_contents(text,matches_lst){
    if(matches_lst.length === 0) { 
        $("#p_parsed_text").append(text.replace(/\n/g,'\n<br>'));
        $("#btn_download").prop('disabled', true);
        $("#btn_save_annotation").prop('disabled', true);
    } else {
        _create_list_from_matches(matches_lst);
        _set_match_totalnum(matches_lst);

        let rows_str = _create_tblrows_from_matches(matches_lst);
        $('#tbl_hpolist').append(rows_str);

        let parsed_text = _format_text_from_matches(text, matches_lst);
        parsed_text = parsed_text.replace(/\n/g,'\n<br>');
        $("#p_parsed_text").append(parsed_text);

        $("#btn_download").prop('disabled', false);
        $("#btn_save_annotation").prop('disabled', false);
    }

    _set_match_totalnum(matches_lst);
}

function _parse_text(note){
    // nomalize user input
    let text = _normalize_text(note);
    _store_normalized_text(text);

    let matches_lst = _search_hpomatch_from_text(text);
    _store_matches(matches_lst);

    _create_and_set_result_contents(text,matches_lst);

    $("#div_ResultsPanel").show();
    
    $("#div_outputPanel").show();

    $('html, body').animate({scrollTop: $("#btn_parse_userinput").offset().top},100);
}

function _remove_match(idx){
    // clear current result contents
    _clear_result_contents();
   
   // remove indicated match from matches list
    _remove_match_from_lst(idx);

    // create new result based on modified match list.
    let normalized_text = _get_normalized_text();
    let matches_lst = _get_matches();
    
    _create_and_set_result_contents(normalized_text,matches_lst); 
}

function _remove_match_from_lst(idx){
    let matches_lst = _get_matches();
    matches_lst.splice(idx,1);
}

function _get_hpoid_from_tbl(idx){

//    let col_hpoid = 0;
//    return $('#tbl_hpolist').find("tr:eq("+idx+")").find("td:eq("+col_hpoid+")").html();
//    return document.getElementById("td_"+idx).innerHTML;
    return  $("#td_"+idx).text();
}
function _remove_hpo(idx){
  
    _hidePopup();
 
    let hpoid = _get_hpoid_from_tbl(idx);
    
   // remove indicated match from matches list
    let matches_lst = _get_matches();
    let filtered = $.grep(matches_lst, function(element, index) {
        return element.id_in_dic !== hpoid;
    });

    _store_matches(filtered);

    // clear current result contents
    _clear_result_contents();

    // create new result based on modified match list.
    let normalized_text = _get_normalized_text();

    _create_and_set_result_contents(normalized_text,filtered); 
}


function _create_list_from_matches(matches_lst) {

    let $ul = $('#ul_matches');

    let symptoms_label_true  = _get_symptoms_label_text(true);
    let symptoms_label_false = _get_symptoms_label_text(false);

    for( let i=0; i<matches_lst.length; i++) {

        let hpo_id       = matches_lst[i].id_in_dic;
        let hpo_english  = matches_lst[i].eterm_in_dic;
        let hpo_japanese = matches_lst[i].jterm_in_dic;
        let term_in_text = matches_lst[i].term_in_text;
        let def          = matches_lst[i].def; 

        let class_from_symptoms = _get_symptoms_class(matches_lst[i].with_symptoms);

        let symptoms_str = _get_symptoms_label_text(matches_lst[i].with_symptoms);

        let $li = $('<li id=\"li_hpo_'+i+'\" onclick=\"_choose_match_from_list('+i+')\">').addClass("list-group-item hpo noselect").appendTo($ul);
        if(class_from_symptoms) $li.addClass(class_from_symptoms);
       
        $('<span><b>'+term_in_text +'&nbsp</b></span>').appendTo($li);

        $('<span>').addClass('hpo_match_title1').appendTo($li);

        let $span_title2 = $('<span>'+ hpo_japanese + '(' + hpo_id + ')</span>').addClass('hpo_match_title2').appendTo($li);

        let $div_ctl_upper = $('<div class=\"dropdown hpo_ctl\" style="color:black;">').appendTo($li);
        $('<span class=\"text2hpoicon-trash\" onclick=\"_remove_match('+i+');\"></span>').appendTo($div_ctl_upper);
        $('<span class=\"text2hpoicon-ellipsis-vert dropdown-toggle\" data-toggle=\"dropdown\">').appendTo($div_ctl_upper);
        let $ul_ctl_upper  = $('<ul class=\"dropdown-menu dropdown-menu-right\"  role=\"menu\" style="margin:0px;padding:0px;">').appendTo($div_ctl_upper);
        let $li_ctl_upper1 = $('<li style=\"cursor: pointer;\" role=\"presentation\">').appendTo($ul_ctl_upper);
        let $a_ctl_upper1  = $('<a onclick=\"_change_match_symptoms_status('+i+',true);\">').appendTo($li_ctl_upper1);
        $('<span class=\"text2hpoicon-flag-empty\">').appendTo($a_ctl_upper1);
        $('<b>' + symptoms_label_true+ '</b>').appendTo($a_ctl_upper1);
        let $li_ctl_upper2 = $('<li style=\"cursor: pointer;\" role=\"presentation\">').appendTo($ul_ctl_upper);
        let $a_ctl_upper2  = $('<a onclick=\"_change_match_symptoms_status('+i+',false);\">').appendTo($li_ctl_upper2);
        $('<span class=\"text2hpoicon-flag-empty\">').appendTo($a_ctl_upper2);
        $('<b>' + symptoms_label_false+ '</b>').appendTo($a_ctl_upper2);


        let $div_hpo_detail = $('<div>').addClass("hpo_detail").appendTo($li);
        $('<span>'+ hpo_id + '&nbsp' + hpo_japanese + '</span>').addClass("hpo_match").appendTo($div_hpo_detail);
        $('<br>').appendTo($div_hpo_detail);
        $('<p style=\"margin-right:10px;margin-top:10px;\">'+ def +'</p>').appendTo($div_hpo_detail);


        let $a1 = $('<a class=\"btn btn-link\"  style=\"color:#00000070;margin-bottom:0px;vertical-align:middle;padding-left:0px;padding-bottom:2px;\" href=\"javascript:void(0);\" onclick=\"_showDetail('+i+');\">').appendTo($div_hpo_detail);
        //$('<span class=\"text2hpoicon-annotation\" style=\"\"><b style=\"color:#00000070\">アノテーションを変更</b></span>').appendTo($a1);
        $('<span class=\"svg-demo\" style=\"font-size:12px;\"><b>アノテーションを変更</b></span>').appendTo($a1);
        $('<label id=\"li_label_hpo_'+i+'\" class=\"label\">'+symptoms_str+'</label>').appendTo($div_hpo_detail);
    }
}


function _showDetail(idx){
    let matches_lst = _get_matches();
    let hpo_id      = matches_lst[idx].id_in_dic  + "_ja";
    let hpo_japanese = matches_lst[idx].jterm_in_dic;

    SELECTED_MATCH_IDX = idx;
    
    $("#tokeninput_hpo").tokenInput("clear");
    $("#tokeninput_hpo").tokenInput("add", {id: hpo_id, name: hpo_japanese});
    $('.token-input-token-term-facebook').trigger('click');
}

SELECTED_MATCH_IDX = -1;
//function _changeHPOforSelectedMatch(id_in_dic,term_in_dic,eterm_in_dic,def){
function _changeHPOforSelectedMatch(hpo_id){

    if(SELECTED_MATCH_IDX<0){
        return;
    }

    let matches_list = _get_matches();

    if(matches_list[SELECTED_MATCH_IDX].id_in_dic === hpo_id){
        // no change
        return;
    }

    let notfound = true;
    let hpo_dic = _get_HPO_DIC();
    for(let i=0; i< hpo_dic.length; i++){
        if(hpo_dic[i].FLAG == 0){
            continue;
        }
        if(hpo_dic[i].HPO_ID === hpo_id){
            matches_list[SELECTED_MATCH_IDX].id_in_dic    = hpo_dic[i].HPO_ID;
            matches_list[SELECTED_MATCH_IDX].term_in_dic  = hpo_dic[i].SEARCH_KEY;
            matches_list[SELECTED_MATCH_IDX].jterm_in_dic = hpo_dic[i].JT;
            matches_list[SELECTED_MATCH_IDX].eterm_in_dic = hpo_dic[i].ET;
            matches_list[SELECTED_MATCH_IDX].def          = hpo_dic[i].DEF;
            notfound = false;
            break;
        }
    }
    
    if(notfound){
        alert("No item in dic for HPO[" + hpo_id + "]");
        return;
    }
    
    //clear list and table
    $("#ul_matches").find("li").remove();
    $("#tbl_hpolist").find("tr:gt(0)").remove();

    //recreate list
    _create_list_from_matches(matches_list);
    _set_match_totalnum(matches_list);

    //recreate table
    let rows_str = _create_tblrows_from_matches(matches_list);
    $('#tbl_hpolist').append(rows_str);

    _choose_match_from_list(SELECTED_MATCH_IDX);

    SELECTED_MATCH_IDX = -1;
}



// mode: match or hpo
function _get_ctl(idx, mode) {
    let symptoms_label_true  = _get_symptoms_label_text(true);
    let symptoms_label_false = _get_symptoms_label_text(false);

    let _remove_func      = "_remove_match";
    let _change_symptoms_status_func = "_change_match_symptoms_status";
    if(mode === "hpo"){
        _remove_func            = "_remove_hpo";
        _change_symptoms_status_func = "_change_hpo_symptoms_status";
    }

    return '<div class=\"dropdown hpo_ctl\">' +
             '<span class=\"text2hpoicon-trash\" onclick=\"'+_remove_func+'('+idx+');\"></span>&nbsp;'+
             '<span class=\"text2hpoicon-ellipsis-vert dropdown-toggle\" data-toggle=\"dropdown\"></span>'+
             '<ul class=\"dropdown-menu dropdown-menu-right\"  role=\"menu\" style=\"margin:0px;padding:0px;\">'+
               '<li style=\"cursor: pointer;\" role=\"presentation\">'+
                 '<a onclick=\"'+_change_symptoms_status_func+'('+idx+',true);\">'+
                   '<span class=\"text2hpoicon-flag-empty\"></span>&nbsp;&nbsp;'+symptoms_label_true+
                 '</a>'+
               '</li>'+
               '<li style=\"cursor: pointer;\" role=\"presentation\">'+
                 '<a onclick=\"'+_change_symptoms_status_func+'('+idx+',false);\">'+
                   '<span class=\"text2hpoicon-flag-empty\"></span>&nbsp;&nbsp;'+symptoms_label_false+
                 '</a>'+
               '</li>'+
             '</ul>'+
           '</div>';
}

function _do_search_disease(){
    let matches_lst = _get_matches();
    let hpo_lst = _get_hpo_with_symptoms(matches_lst);

    if(hpo_lst.length === 0){
        alert("No HPOs(with symptoms)");
        return;
    }

    let url = "https://pubcasefinder.dbcls.jp/search_disease/phenotype:" + 
              hpo_lst.join('_ja%2C') +'_ja'+
              "/gene:/page:1,1,1,1/size:10,10,10,10,omim";
    window.open(url);
    //var form = document.createElement('form');
    //form.action = url;
    //form.target = '_blank';
    //form.method = 'POST';
    //document.body.appendChild(form);
    //form.submit(); 
}


function _get_hpo_with_symptoms(matches_lst) {
    let tbldata = _create_tbldata_from_matches(matches_lst);

    let hpo_lst = [];
    Object.keys(tbldata).sort().forEach(function (hpo_id) {
        if(tbldata[hpo_id].symptoms){
            hpo_lst.push(hpo_id);
        }
    });

    return hpo_lst;
}

function _create_tbldata_from_matches(matches_lst) {
    let tbldata = {};
    for( let i=0; i<matches_lst.length; i++) {

        let hpo_id    = matches_lst[i].id_in_dic;
        let hpo_str   = matches_lst[i].jterm_in_dic;
        let hpo_str_e = matches_lst[i].eterm_in_dic; 
        let symptoms  = matches_lst[i].with_symptoms;

        if(tbldata[hpo_id]){
            if(symptoms == false){
                tbldata[hpo_id].symptoms = symptoms;
            }
            tbldata[hpo_id].match_count = tbldata[hpo_id].match_count + 1; 
        }else {
            tbldata[hpo_id] = {
                "hpo_str":   hpo_str,
                "hpo_str_e": hpo_str_e,
                "symptoms" : symptoms,
                "match_count" : 1
            };
        }
    }
    return tbldata;
}
function _create_tblrows_from_matches(matches_lst) {

    let tbldata = _create_tbldata_from_matches(matches_lst);
    _set_hpo_totalnum(tbldata);

    let rows_str = "";

    let j = 1;
    Object.keys(tbldata).sort().forEach(function (hpo_id) {
        let hpo_str   = tbldata[hpo_id].hpo_str;
        let hpo_str_e = tbldata[hpo_id].hpo_str_e;
        let num       = tbldata[hpo_id].match_count ;

        let symptoms_str = _get_symptoms_label_text(tbldata[hpo_id].symptoms);

        let class_from_symptoms = _get_symptoms_class(tbldata[hpo_id].symptoms);

        rows_str = rows_str + '<tr>'  + 
                                '<td id=\"td_'+j+'\" class=\"hpo_id '+ class_from_symptoms +'\">' + hpo_id + '</td>' +
                                '<td>' + hpo_str   + '</td>' + 
                                '<td>' + hpo_str_e + '</td>' + 
                                '<td style=\"vertical-align:middle;\" class=\"'+class_from_symptoms+'\"><span class=\"label '+class_from_symptoms+'\" id=\"tbl_label_hpo_'+j+'\">'+symptoms_str+'</span></td>' + 
                                '<td>' + num + '</td>' +
                                '<td>'+ _get_ctl(j,"hpo") + '</td>' +
                              "</tr>";
        j++;
    });
    return rows_str;
}


function _format_text_from_matches(normalized_text, matches_lst) {

    let formated_text = "";
    let current_start_pos = 0;

    for( let i=0; i<matches_lst.length; i++) {
        let start   = matches_lst[i].start;
        let end     = matches_lst[i].end;

        let before_str = normalized_text.substring(current_start_pos, start);
        let hpo_str =  normalized_text.substring(start, end + 1);

        formated_text = formated_text + before_str;

        let class_from_symptoms = _get_symptoms_class(matches_lst[i].with_symptoms);
        formated_text = formated_text + '<span class=\"'+class_from_symptoms+'\" ' +
                        ' id=\"span_hpo_'+i+'\" onclick=\"_choose_match_from_textarea('+i+');\">' + hpo_str + '</span>';
       
        current_start_pos = end + 1;
    }

    if(current_start_pos < normalized_text.length -1){
        let str = normalized_text.substring(current_start_pos);
        formated_text = formated_text + str;
    }

    return formated_text;
}

// change the symtoms status of math with idx at list
function _change_match_symptoms_status(idx,symptoms_status) {

    let matches_lst = _get_matches();
    matches_lst[idx].with_symptoms = symptoms_status;

    let class_for_withoutsymptoms = _get_symptoms_class(false);
    let symptoms_str  = _get_symptoms_label_text(symptoms_status);
    
    
    $("#span_hpo_"+idx).removeClass(class_for_withoutsymptoms);
    if(symptoms_status) {
        //default with symptoms
    } else {
        // withoutsymptoms
        $("#span_hpo_"+idx).addClass(class_for_withoutsymptoms);
    } 
    
    $("#li_hpo_"+idx).removeClass(class_for_withoutsymptoms);
    if(symptoms_status) {
        // default
    } else {
        $("#li_hpo_"+idx).addClass(class_for_withoutsymptoms);
    }
    $("#li_label_hpo_"+idx).text(symptoms_str);

    $("#tbl_hpolist").find("tr:gt(0)").remove();
    let rows_str = _create_tblrows_from_matches(matches_lst);
    $('#tbl_hpolist').append(rows_str);

    _set_match_totalnum(matches_lst);
}

function _change_hpo_symptoms_status(idx,symptoms_status) {

    _hidePopup();

    let hpoid = _get_hpoid_from_tbl(idx);

    let class_for_withoutsymptoms = _get_symptoms_class(false);
    let symptoms_str  = _get_symptoms_label_text(symptoms_status);
    
    let matches_lst = _get_matches();
    for(let i=0;i<matches_lst.length;i++){
        if(matches_lst[i].id_in_dic === hpoid){
            matches_lst[i].with_symptoms = symptoms_status;

            $("#span_hpo_"+i).removeClass(class_for_withoutsymptoms);
            if(symptoms_status) {
                //default with symptoms
            } else {
                // withoutsymptoms
                $("#span_hpo_"+i).addClass(class_for_withoutsymptoms);
            } 

            $("#li_hpo_"+i).removeClass(class_for_withoutsymptoms);
            if(symptoms_status) {
                // default
            } else {
                $("#li_hpo_"+i).addClass(class_for_withoutsymptoms);
            }
            $("#li_label_hpo_"+i).text(symptoms_str);

        }
    }
   
    $("#td_"+idx).removeClass(class_for_withoutsymptoms);
    $("#tbl_label_hpo_"+idx).removeClass(class_for_withoutsymptoms);
    if(symptoms_status) {
        // default
    } else {
        $("#tbl_label_hpo_"+idx).addClass(class_for_withoutsymptoms);
        $("#td_"+idx).addClass(class_for_withoutsymptoms);
    }
    $("#tbl_label_hpo_"+idx).text(symptoms_str);

    let tbldata = _create_tbldata_from_matches(matches_lst);
    _set_hpo_totalnum(tbldata);
}

function _get_symptoms_label_text(symptoms_status) {
    let ret_str = _normalize_text("症状なし");
    if(symptoms_status){
        ret_str = _normalize_text("症状あり");
    }
    return ret_str;
}

function _get_symptoms_class(symptoms_status) {
    let ret_str = "without_symptoms";
    if(symptoms_status){
        // default 
        ret_str = "";
    }
    return ret_str;
}

function _clear_match_chosen_status() {
    $("#p_parsed_text>span.chosen").removeClass("chosen");
    $("#ul_matches>li.chosen").removeClass("chosen");
}

function _add_match_chosen_status(idx) {
    $("#span_hpo_" + idx).addClass('chosen');
    $("#li_hpo_" + idx).addClass('chosen');
}

function _choose_match_from_textarea(idx){

    _clear_match_chosen_status();
    _add_match_chosen_status(idx);

    let element = document.getElementById("li_hpo_" + idx);
    if(element) element.scrollIntoViewIfNeeded();
}

function _choose_match_from_list(idx){
    _clear_match_chosen_status();
    _add_match_chosen_status(idx);
    let element = document.getElementById("span_hpo_" + idx);
    if(element) element.scrollIntoViewIfNeeded();
}

function _load_HPO_DIC_from_server(_parse_text,note){
    let succeed = true;

    $.LoadingOverlay("show");

//    $.getJSON("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.v2.json")
//    $.get("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.v2.tsv")
//    $.get("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.withengkey.v3.tsv")
//    $.get("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.withengkey.v4.tsv")
//    $.get("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.withengkey.v5.tsv")
//    $.get("/static/data/HPO-japanese.alpha.18Oct2017.withkeyandparents.withengkey.v6.tsv")
      $.get(HPO_DIC)
        .done(function(data) {
           let jsondata = _tsv2JSON(data);
           _store_HPO_DIC(jsondata);
           if(typeof(note)!=="undefined"){
               _parse_text(note);
           }
        })
        .fail(function(errorThrown ) {
            alert(errorThrown);
            succeed = false;
        })
        .always(function() {
           $.LoadingOverlay("hide"); 
        });
        
    return succeed;
}
var hpo_dic_json = [];
function _store_HPO_DIC(data) {
    hpo_dic_json = data;
}

function _get_HPO_DIC(){
    return hpo_dic_json;
}

var normalized_text = "";
function _store_normalized_text(text){
    normalized_text = text;
}

function _get_normalized_text(){
    return normalized_text;
}

function _clear_normalized_text(){
    normalized_text = "";
}


function _normalize_text(note) {
    if(note.length === 0) return "";
    //let parsed_text=note.replace(/\s+/g,'');
    //parsed_text =jaconv.normalize(parsed_text);
    let parsed_text = jaconv.normalize(note);
    if ( String.prototype.normalize ) {
      parsed_text = parsed_text.normalize("NFKC");
    }
    return parsed_text;
}


var matches = [];
function _store_matches(matches_lst) {
    matches = matches_lst;
}

function _get_matches() {
    return matches;
}

function _clear_matches() {
    matches.length = 0;
}


function _search_hpomatch_from_text(text) { 
    let text1 = text.toUpperCase();
 
    let matches_lst = [];
    let idx_hashtable = {};

    let hpo_dic = _get_HPO_DIC();
    $.each(hpo_dic, function(i, item) {
/* item 
    {
         "SEARCH_KEY": "吻",
         "PARENTS": "",
         "HPO_ID": "HP:0012806",
         "ET": "Proboscis",
         "JT": "吻",
         "DEF": "A fleshy, tube-like structure usually located in the midline of the face or just to one side of the midline. [HPO:probinson, PMID:19152422]"
    }
    {
         "SEARCH_KEY": "PROBOSCIS",
         "PARENTS": "",
         "HPO_ID": "HP:0012806",
         "ET": "Proboscis",
         "JT": "吻",         "DEF": "A fleshy, tube-like structure usually located in the midline of the face or just to one side of the midline. [HPO:probinson, PMID:19152422]"
    }

 */
//       console.log(item.no); 
//       let hpo_term = _normalize_text(item.SEARCH_KEY);
        let hpo_term = item.SEARCH_KEY;

        if(hpo_term.length > 0){

            // check if longer was chosen already.
            let none_longer_found = true;            
            let long_lst_str = item.PARENTS;
            if(long_lst_str.length > 0) {
                let long_lst = long_lst_str.split(",");
                for(let j = 0; j < long_lst.length; j++){
                    let key = 'idx_'+ long_lst[j];
                    if(idx_hashtable[key]){
                        none_longer_found = false;
                        break;
                    }
                } 
            }

            if(none_longer_found){
                let counter = 0;
                for(let pos = text1.indexOf(hpo_term); pos !== -1; pos = text1.indexOf(hpo_term, pos + 1)) {
                    let term_in_text = text.substring(pos, pos + hpo_term.length);
                    let obj = {start:         pos,
                                end:           pos + hpo_term.length -1,
                                id_in_dic:     item.HPO_ID,
                                term_in_dic:   hpo_term,
                                eterm_in_dic:  item.ET,
                                jterm_in_dic:  item.JT,
                                term_in_text:  term_in_text,
                                def:           item.DEF,
                                with_symptoms: true
                    };
                    matches_lst.push(obj);
                    counter = counter + 1;
                }

                if(counter > 0){
                    let key = 'idx_'+i;
                    idx_hashtable[key] = counter;
                }
            }
        }
    });

    idx_hashtable.length = 0;

    // Startの順にソート（昇順）
    _sort_match(matches_lst);
    
    //_remove_overlap(matches_lst);
    return matches_lst;
}

function _sort_match(matches){
    matches.sort(function(a, b) {
        if (a.start < b.start) return -1;
        if (a.start > b.start) return 1;
        if (a.end < b.end) return -1;
        if (a.end > b.end) return 1;
        return 0;
    });
}

function _modify_matchrange_from_selectedtext(rangeStart,rangeEnd) {

    let matches_list = _get_matches();
    let overlap_lst = _find_overlap(rangeStart,rangeEnd,matches_list);
    if(overlap_lst.length === 0){return false;}
    for(let i=overlap_lst.length-1; i > 0; i--){
        matches_list.splice(overlap_lst[i],1);
    }
    let idx = overlap_lst[0];
    matches_list[idx].start = rangeStart;
    matches_list[idx].end   = rangeEnd;

    let normalized_text = _get_normalized_text();    
    matches_list[idx].term_in_text = normalized_text.substring(rangeStart, rangeEnd + 1); 

    _clear_result_contents();
   
    // create new result based on modified match list.
    _create_and_set_result_contents(normalized_text,matches_list); 

    _choose_match_from_textarea(idx);
}

var matches_from_server = [];

function _load_match_from_server(rangeStart,rangeEnd) {
    _hidePopup();
   

    if(rangeEnd - rangeStart + 1 > SERVER_POST_LIMIT){

        alert("一度に解析できる文字数は"+SERVER_POST_LIMIT+"文字までです");

        return;
    }
 
    let normalized_text = _get_normalized_text();    
    let term_in_text = normalized_text.substring(rangeStart, rangeEnd + 1);
     
    $.LoadingOverlay("show");
    
    matches_from_server.length = 0;

    //$.post("/get_hpo_by_text","text=" + encodeURI(term_in_text))
    //$.post("https://dev-pubcasefinder.dbcls.jp/get_hpo_by_text","text=" + encodeURI(term_in_text))
    $.post(SERVER_POST_URL,"text=" + encodeURI(term_in_text))
        .done(function(data1,textStatus,jqXHR) {
            //format of data1
            //hpoid1,hpoid2,hpoid3,hpoid4
            if(data1 && data1 !== 'none'){
                let data2 = data1.replaceAll('_ja','').split(',');
                _create_popuplist(data2,rangeStart,rangeEnd);
            }else{
                alert("No match found for [" + term_in_text + "]");
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown ) {
            alert('Error:' + jqXHR.status + ":" + textStatus + ":" +errorThrown +"\nPlease check URL!");
        })
        .always(function() {
            $.LoadingOverlay("hide"); 
        });
}   

function _create_popuplist(hpolst_from_server,rangeStart,rangeEnd){
    let hpo_dic = _get_HPO_DIC();

    let $ul = $("#ul_popup");
    $ul.find("li").remove();

    matches_from_server.length = 0;

    let num = 0;
    let li_str = "";
    for(let idx=0; idx < hpolst_from_server.length; idx++){
        let hpo_id = hpolst_from_server[idx];
        for(let i=0; i< hpo_dic.length; i++){
            if(hpo_dic[i].HPO_ID === hpo_id){
                let obj = {HPO_ID:     hpo_id,
                           SEARCH_KEY: hpo_dic[i].JT,
                           JT:         hpo_dic[i].JT,
                           ET:         hpo_dic[i].ET,
                           DEF:        hpo_dic[i].DEF
                };
                matches_from_server.push(obj);

                li_str = li_str + '<li>' + 
                                  '<a onClick=\"_add_match('+rangeStart +','+rangeEnd+','+ num +');\">'+
                                      hpo_dic[i].JT + ' ('+ hpo_dic[i].ET +')' +
                                  '</a>'+
                              '</li>';    

//                let $li = $('li').appendTo($ul);
//		let $a = '<a onClick=\"_add_match('+rangeStart +','+rangeEnd+','+ num +');\">'+ hpo_dic[i].JT + ' ('+ hpo_dic[i].ET +')<\/a>';
//                $($a).appendTo($li);
                num++;
		break;
            }
        }
    }
    
    if(num > 0) {
	$('#ul_popup').append(li_str);
        $("#div_selectionPopup").css("display","block");
    }else{
	alert("No match found.");
    }
}



function _add_match(rangeStart,rangeEnd,idx) {
    let normalized_text = _get_normalized_text();    
    let term_in_text = normalized_text.substring(rangeStart, rangeEnd + 1);
    
    let matches_list = _get_matches();
    let overlap_lst = _find_overlap(rangeStart,rangeEnd,matches_list);
    if(overlap_lst.length > 0){
      for(let i=overlap_lst.length-1; i >= 0; i--){
        matches_list.splice(overlap_lst[i],1);
      }
    }
    let obj = {start:         rangeStart,
               end:           rangeEnd,
               id_in_dic:     matches_from_server[idx].HPO_ID,
               term_in_dic:   matches_from_server[idx].SEARCH_KEY,
               jterm_in_dic:  matches_from_server[idx].JT,
               eterm_in_dic:  matches_from_server[idx].ET,
               def:           matches_from_server[idx].DEF,
               term_in_text:  term_in_text,
               with_symptoms: true
    };
    matches_list.push(obj);
    _sort_match(matches_list);

    _clear_result_contents();
   
    _create_and_set_result_contents(normalized_text,matches_list); 

    // find idx and call select
    for(let i=0; i<matches_list.length; i++){
        let start_m = matches_list[i].start;
        let end_m   = matches_list[i].end;

        if(start_m === rangeStart && end_m === rangeEnd){
            _choose_match_from_list(i);
            let element = document.getElementById("li_hpo_" + i);
            if(element) element.scrollIntoViewIfNeeded();
            break;
        }
    }
    //_choose_match_from_list
}

function _find_overlap(start,end,matches_list){
    let retLst = [];
    for(let i=0; i<matches_list.length; i++){
        let start_m = matches_list[i].start;
        let end_m   = matches_list[i].end;

        if(end < start_m || start > end_m){
            //
        }else{
            retLst.push(i);
        }
    }
    return retLst;
}

function _remove_overlap(matches_list) {

    for(let i=matches_list.length -1; i>=1; i--){
        let start = matches_list[i].start;
        let end   = matches_list[i].end;

        let overlap = false;
        for(let j=i-1; j>=0; j--){
            let start_f = matches_list[j].start;
            let end_f   = matches_list[j].end;

            if(start <= end_f){
                overlap = true;
                break;
            }
        }

        if(overlap) {
            matches_list.splice(i,1);
        }
    }
}

function _getSelectionCharOffsetsWithin(element) {
    let start = 0, end = 0;
    let text ="";
    let sel, range, priorRange;
    if (typeof window.getSelection !== "undefined") {
        let stmp = window.getSelection();
        if(stmp.type !== "None"){ 
            //range = window.getSelection().getRangeAt(0);
            range = stmp.getRangeAt(0);
            priorRange = range.cloneRange();
            priorRange.selectNodeContents(element);
            priorRange.setEnd(range.startContainer, range.startOffset);
            start = priorRange.toString().length;
            end = start + range.toString().length;
            text = range.toString();
        }
    } else if (typeof document.selection !== "undefined" && (sel = document.selection).type !== "Control") {
        range = sel.createRange();
        priorRange = document.body.createTextRange();
        priorRange.moveToElementText(element);
        priorRange.setEndPoint("EndToStart", range);
        start = priorRange.text.length;
        end = start + range.text.length;
        text = range.text;
    }

    return {'start': start, 'end': end -1, 'text':text};
}

function _clearSelection(){
    if(window.getSelection) {
        return window.getSelection().removeAllRanges();
    } else if(document.getSelection) {
        return document.getSelection().removeAllRanges();
    } else {
        document.selection.removeAllRanges();
    }
}

function _create_phenopacket(tbldata){

    let phenopacket = {};
    
    let timestamp = _getTimeStamp();
    // id
    phenopacket.id = "phenopacket-" + timestamp;
     
    // phenotypic_features
    phenopacket.phenotypic_features = [];
    
    Object.keys(tbldata).sort().forEach(function (hpo_id) {
        let hpo_str     = tbldata[hpo_id].hpo_str;
        let hpo_str_e   = tbldata[hpo_id].hpo_str_e;
        let symptoms    = tbldata[hpo_id].symptoms;
        let match_count = tbldata[hpo_id].match_count;
        let negated     = (!symptoms);
        let obj = {
            "description" : "phenotype("+hpo_str_e+") found in document with " + match_count + " matches.",
            "type" : {
                "id" : hpo_id,
                "label" : hpo_str,
            },
            "negated": negated
        };
        
        phenopacket.phenotypic_features.push(obj);
    });
    
    // meta_data
    phenopacket.meta_data = {
        "created": timestamp,
        "created_by" : "text2hpo",
        "resources": [{
            "id": "hp_jp",
            "name": "Human Phenotype Ontology in Japanese (HPO-Japanese)",
            "url": "https://github.com/ogishima/HPO-Japanese/blob/master/HPO-japanese.alpha.18Oct2017.tsv",
            "version": "2017-10-18",
            "namespacePrefix": "HP",
            "iriPrefix": "http://purl.obolibrary.org/obo/HP_"
          }, {
            "id": "def",
            "name": "human phenotype ontology",
            "url": "http://purl.obolibrary.org/obo/hp.obo",
            "version": "2021-01-08",
            "namespacePrefix": "HP",
            "iriPrefix": "http://purl.obolibrary.org/obo/HP_"
          }]	
    };
    
    return phenopacket;
}

function _save_matches(type){

    let matches_list = _get_matches();

    let tbldata = _create_tbldata_from_matches(matches_list);

    let content = "";
    if(type === 'json'){
        content = JSON.stringify(_create_phenopacket(tbldata));
    } else if(type === 'tsv'){
        content = 'HPO_ID\t症状名(日本語)\t症状名(英語)\t症状の有無\tカウント\n';
        Object.keys(tbldata).sort().forEach(function (hpo_id) {
            let hpo_str     = tbldata[hpo_id].hpo_str;
            let hpo_str_e   = tbldata[hpo_id].hpo_str_e;
            let symptoms    = tbldata[hpo_id].symptoms;
            let match_count = tbldata[hpo_id].match_count;
            content = content +  hpo_id       + '\t' +
                                 hpo_str      + '\t' +
                                 hpo_str_e    + '\t' +
                                 symptoms     + '\t' +
                                 match_count  + '\n';
            
        });
    } else {
        // csv
        content = '\"HPO_ID\",\"症状名(日本語)\",\"症状名(英語)\",\"症状の有無\",\"カウント\"\n';
        Object.keys(tbldata).sort().forEach(function (hpo_id) {
            let hpo_str   = tbldata[hpo_id].hpo_str;
            let hpo_str_e = tbldata[hpo_id].hpo_str_e;
            let symptoms  = tbldata[hpo_id].symptoms;
            let match_count = tbldata[hpo_id].match_count;
            content = content + '\"' +  hpo_id       + '\",' +
                                '\"' +  hpo_str      + '\",' +
                                '\"' +  hpo_str_e    + '\",' +
                                '\"' +  symptoms     + '\",' +
                                '\"' +  match_count  + '\"\n';
            
        });
    }
    
    let format_str = _getTimeStamp();                                                                                                        
    let filename = "HPO_result-" + format_str + "." + type;

    _save_text(filename,content);
}

function _save_text(filename, content){
  let dlTarget = new Blob([content],{type:'text/plain'});
  if (window.navigator.msSaveBlob) {
    // IE,Edge
    window.navigator.msSaveBlob(dlTarget, filename);
  } else {
    let a = document.createElement("a");
    a.href = window.URL.createObjectURL(dlTarget);
    a.download = filename;
    e = document.createEvent('MouseEvent');
    e.initEvent("click",true,true);
    a.dispatchEvent(e);
    let agent = window.navigator.userAgent.toLowerCase();
    if(agent.indexOf('firefox') !== -1){
      document.body.removeChild(a); // Firefoxで必要
    }
    URL.revokeObjectURL(a.href);
  }
}


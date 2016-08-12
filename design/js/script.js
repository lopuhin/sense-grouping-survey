var current_part = 1;
var err = false
$(document).ready(function(e){              
  $(".submit").on('click', function(){
    check($(this))
  })
})

var check = function(this_button){ 
  if(current_part==2){
    var form_id = this_button.parent()[0].id
    var str = $('#'+form_id).serialize().split('_')
    var inputs = $("#"+form_id).find('.input')

    inputs.each(function(){
      var val = $(this).val()
      if (val == ''){
        err = true
        alert("Заполните все поля")
        return false}
      else{
        err = false
      }
    })
    if(err == false){
      var age = $('[name = "_age"]').val()
      console.log(age)
      if (age<17 || age>70) {
        alert("в исследовании могут принимать участие лица от 16 до 70 лет")
      }else{
        send_ajax(str)
        change_part()
      }
    }
  } 
  else{
    change_part()
  }
}

var send_ajax = function(str){
  console.log(str)
  /*$.ajax({
    type: 'POST',
    url: url,
    data: str,
    success: change_part();
  });*/

}
var change_part=function(){
$(".part"+current_part).removeClass('open')
  $(".part"+current_part).addClass('hide')
  current_part++
  $(".part"+current_part).addClass('open')
}

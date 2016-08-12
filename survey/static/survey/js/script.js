var current_part = 1;

$(document).ready(function(e){
  $(".submit").on('click', function(){
    check($(this))
  })
})

var check = function(this_button){
  if(current_part==2){
    var form_id = this_button.parent()[0].id
    var $form = $('#' + form_id);
    var inputs = $form.find('.input')
    var err = false;

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
      var age = $('[name = "age"]').val()
      if (age<17 || age>70) {
        alert("В исследовании могут принимать участие лица от 17 до 70 лет")
      }else{
        send_ajax($form);
      }
    }
  }
  else{
    change_part()
  }
}

var send_ajax = function ($form) {
  $.ajax({
    url: '/',
    method: 'POST',
    data: $form.serialize(),
    success: function (response) {
      $('#next').attr('href', response.next);
      change_part();
    }
  });

}
var change_part=function(){
$(".part"+current_part).removeClass('open')
  $(".part"+current_part).addClass('hide')
  current_part++
  $(".part"+current_part).addClass('open')
}



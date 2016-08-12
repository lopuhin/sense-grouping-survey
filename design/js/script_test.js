var number_groups = 1
var title = "Гранат"
var words = [
"спелый гранат",
"вкусные гранаты",
"почистить гранат",
"съесть гранат",
"посадить гранат",
"цветущие гранаты",
"Гранаты любят тепло",
"В саду росли гранаты",
"неограненный гранат",
"добывать гранат",
"месторождение граната",
"ожерелье из граната"
]
var result={
  group_1:[],
  group_2:[],
  group_3:[],
  group_4:[],
  group_5:[],
  group_6:[],
  group_7:[],
  group_8:[],
  group_9:[],
  group_10:[],
}

$(document).ready(function(){
 
  $(".new_group").on("click", function(){
    create_group();
  })
  $(".next_group").on("click", function(){
    next_group();
  })
   push_words();
   var color = generate()
   $('.groups').css('background-color',color)
}); 
  
var push_words = function(){
  $('.title').html(title)
  for (var i =1; i<=10; i++) {
    $('#mess_'+i).html(words[i-1])
  };
}
var create_group=function(){

  if (number_groups>=10 || $("#section > p").length==0) {alert('максимальное количество групп созданно')}
    else{
      number_groups++;
      var color = generate()
      $("#groups").append('<div class="groups" style="background-color:'+color+'"><div name="text" id="group_'+number_groups+'" class="user_group"  cols="30" rows="10" ondragenter="return dragEnter(event)" ondrop="dragDrop1(event)" ondragover="return dragOver(event)"></div></div>')
      
    }
}
var next_group = function(){
  if ($("#section > p").length==0) {
    for (var i = 1; i <= 10; i++) {
        var mess = $('#mess_'+i).html()
        var group = $('#mess_'+i).parent()
        var id = group[0].id
        result[id].push(mess)
    };
    console.log(result)
   $.ajax({
    type: 'POST',
    url: url,
    data: result,
    success: push_words()
  });

  };
}
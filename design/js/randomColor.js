var generate = function(){
  var r;
  var g;
  var b;

  r=randomInteger()
  g=randomInteger()
  b=randomInteger()

  var color = "rgba("+r+","+g+","+b+",0.3)"
  return color;

}
function randomInteger() {
  var rand = 60 + Math.random() * (200 - 50)
  rand = Math.round(rand);
  return rand;
}
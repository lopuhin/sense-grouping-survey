var number_groups, max_groups;

$(document).ready(function(){
    $('.new_group').on('click', function(){
        create_group();
    });
    $('.next_group').on('click', function(){
        next_group();
    });
    push_words();
});

function push_words() {
    if (to_group.length === 0) {
        window.location = feedback_url;
        return;
    }
    var $parent = $('#section');
    $parent.children().remove();
    var group = to_group.pop();
    max_groups = group.contexts.length;
    number_groups = 0;
    $('#groups').children().remove();
    create_group();
    $('.next_group').addClass('disabled');
    var progressMessage = (done_contexts + 1) + ' из ' + total_to_group;
    $parent.append('<div class="progress">' + progressMessage + '</div>');
    $parent.append('<h1 class="title">' + group.word + '</h1>');
    for (var i = 0; i < group.contexts.length; i++) {
        var context = group.contexts[i];
        $parent.append(
            '<p class="drag" id="ctx_' + context.id +
            '" draggable="true" ondragstart="return dragStart(event)">' +
            context.text + '</p>');
    }
}

function create_group() {
  if (number_groups >= max_groups) {
      alert('Максимальное количество групп создано.')
  } else {
      number_groups += 1;
      var color = randomColor({
         luminosity: 'light',
         format: 'rgba'
      });
      $("#groups").prepend(
          '<div class="groups" style="background-color:' +
          color + '">' +
          '<div id="group_' + number_groups +
          '" class="user_group"  cols="30" rows="10" ' +
          'ondragenter="return dragEnter(event)" ' +
          'ondrop="return ctxDragDrop(event)" ' +
          'ondragover="return dragOver(event)">' +
          '</div></div>');
    }
}

function all_grouped() {
    return $('#section').find('>p').length === 0;
}

function next_group() {
    if (all_grouped()) {
        var grouping = {};
        $('p.drag').each(function (idx, el) {
            var group_id = $(el).parent()[0].id.split('_')[1];
            if (!grouping[group_id]) {
                grouping[group_id] = [];
            }
            grouping[group_id].push(el.id.split('_')[1]);
        });
        $.ajax({
            type: 'POST',
            url: './',
            data: {
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val(),
                grouping: JSON.stringify(grouping)
            },
            success: function () {
                done_contexts += 1;
                push_words();
            }
        });
    }
}

var dragged_id;

function dragStart(ev) {
    ev.dataTransfer.effectAllowed = 'move';
    ev.dataTransfer.dropEffect = 'move';
    ev.dataTransfer.setData('Text', ev.target.getAttribute('id'));
    dragged_id = ev.target.getAttribute('id');
    // $('#' + dragged_id).css('color', '#999');
    return true;
}

function dragEnter(ev) {
    ev.preventDefault();
    return true;
}

function dragOver(ev) {
    ev.preventDefault();
    return true;
}

function ctxDragDrop(ev) {
    var $target = $(ev.target);
    if ($target.hasClass('user_group') || $target.hasClass('mess_group')) {
        ev.target.appendChild(document.getElementById(dragged_id));
    } else if ($target.hasClass('drag')) {
        $target.parent()[0].appendChild(document.getElementById(dragged_id));
    }
    set_circle_size(dragged_id);
    set_next_button_state();
    // $('#' + dragged_id).css('color', 'black');
    ev.stopPropagation();
    return false;
}

function set_circle_size(id) {
    var group = $('#' + id).parent();
    var k = group.parent();

    var width = group.width();
    var height = group.height();
    var hp = height/100*10 + height;
    var wp = width/100*10 + width;

    if (width<height && group.hasClass('user_group')) {
        k.css('width',hp)
    }
    if (width>height && group.hasClass('user_group')) {
        k.css('height',wp )
    }
}

function set_next_button_state() {
    var $btn = $('div.next_group');
    if (all_grouped()) {
        $btn.removeClass('disabled');
    } else {
        $btn.addClass('disabled');
    }
}

$(document).ready(function(){
  $("#frmClassList > option").each(function() {
    this.text = this.text.replace(/"/g, '');
    this.value = this.value.replace(/"/g, '');
  });
});


$("#frmClassInfo").on( "submit", function(e) {
   e.preventDefault();

   $('.colSched').html("");

   var obj = new Object();
   obj.classNum = $('#frmClassNum').val();
   obj.classList = $('select#frmClassList').val();

   $.ajax({
     url: "",
     type: "POST",
     data: JSON.stringify(obj),
     contentType: "application/json; charset=utf-8",
     success: function(dat) { updateTable(dat); }
   });
});


function updateTable(data) {
  console.log(data);
  var output = "";

  var obj = JSON.parse(data);
  $.each( obj, function( schedIndex, schedule) {
    var index = schedIndex+1;
    output += '<header><h3> Schedule ' + index + '</h3>' + '<span> Longest&nbsp;Day: ' + schedule.stats.longestDay + '</span></header>';
    output += txtTableHead;

    $.each( schedule.sched, function( timeIndex, hourData) {
    output += '<tr>'

      $.each( hourData, function( day, unit) {
          if (day == 0 ) {
            output += '<th scope="row">' + unit +'</th>'
          }
          else {
            output += '<td>' + unit + '</td>'
          }
      });

    output += '</tr>'
    });

  output += txtTableFoot;
  });

$('.colSched').html(output);
};


txtTableHead = '<table class="table table-striped table-bordered table-sm" cellspacing="0" width="100%">\
  <thead class="thead-dark">\
    <tr>\
      <th scope="col">Time</th>\
      <th scope="col">Mon</th>\
      <th scope="col">Tue</th>\
      <th scope="col">Wed</th>\
      <th scope="col">Thu</th>\
      <th scope="col">Fri</th>\
    </tr>\
  </thead>\
  <tbody>'

txtTableFoot = '</tbody>\
  </table>'

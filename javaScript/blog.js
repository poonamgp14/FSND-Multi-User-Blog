function editCommentClicked(id){

	var divHtml = $('#'+ id).html();
	var actionUrl = '/blog/comment/' + id + '/edit';
	console.log(actionUrl)
	var form = $("<form/>",{
		action: actionUrl,
		method:'post',
		id: id + '-edit-form'
	})
	var editableText = $("<input />",{
		name: 'newCommentContent'
	});
	editableText.val(divHtml);
	editableText.addClass('panel-body editableDiv')
	form.append(editableText);
	form.append($("<input>",{
		type:'submit',
		name: 'submitCommentEdited',
		value: 'Done'
	}));
	form.append($("<input>",{
		type:'button',
		name: 'cancelCommentEdited',
		value: 'Cancel'
	}));

	$('#'+ id).replaceWith(form);

	$("input[name='cancelEditedText']").click(function(e){
		var viewableText = $("<div>",{
			id: id
		});
		viewableText.html(divHtml);
		$( '#'+ id + '-edit-form').replaceWith(viewableText);
	});

	editableText.focus();
}






function editClicked(id){

	var divHtml = $('#'+ id).html();
	actionUrl = '/blog/' + id;
	var form = $("<form/>",{
		action:actionUrl,
		method:'post',
		id: id + '-edit-form'
	})
	var editableText = $("<textarea />",{
		name: 'newPostContent'
	});
	editableText.val(divHtml);
	editableText.addClass('panel-body editableDiv')
	form.append(editableText);
	form.append($("<input>",{
		type:'submit',
		name: 'submitEditedText',
		value: 'Done'
	}));
	form.append($("<input>",{
		type:'button',
		name: 'cancelEditedText',
		value: 'Cancel'
	}));

	$('#'+ id).replaceWith(form);

	$("input[name='cancelEditedText']").click(function(e){
		var viewableText = $("<div>",{class:'panel-body',
			id: id
		});
		viewableText.html(divHtml);
		$( '#'+ id + '-edit-form').replaceWith(viewableText);
	});

	editableText.focus();
}

// function editableTextCancelled(id,divHtml) {
// 	console.log(id);
// 	console.log(divHtml)
// 	var viewableText = $("<div>",{class:'panel-body',
// 		id: id
// 	});
// 	viewableText.html(divHtml);
// 	$('textarea.editableDiv').replaceWith(viewableText);
// };

//query DOM to get the blog id
	//attach it to ur
	var count= 'comments-on-post-'.length;
	// console.log($('#'+ id).parents("[id^=comments-on-post-]").attr('id').substring(count));
	//var blogId = $('#'+ id).parents("[id^=comments-on-post-]").attr('id').substring(count);

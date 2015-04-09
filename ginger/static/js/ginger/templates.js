
define(["jquery", "underscore", "backbone"], function(){

	_.templateSettings = {
  		'interpolate':/\{\{(.+?)\}\}/g,
  		'evaluate':/\{%(.+?)%\}/g
	};

	var templateCache = {}, globalContext = {};

	function Template(name){
		var html = $(name).first().html();
		this.content = _.template(html);
	}

	_.extend(Template.prototype, {
		render: function (context) {
			var ctx = _.extend({},globalContext, context);
		 	return this.content(ctx);
		}
	});

	function getTemplate(name){
		if(!(name in templateCache)){
			templateCache[name] = new Template(name);
		}
		return templateCache[name];
	}

    function renderTemplate(name, context){
        return getTemplate(name).render(context);
    }

    function registerTemplateFunction(name, func){
        	globalContext[name] = callback;
    }

	return {
		"render": renderTemplate,
		"getTemplate": getTemplate,
		"register": registerTemplateFunction
	}

})
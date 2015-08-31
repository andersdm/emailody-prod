'use strict';

// Declare app level module which depends on views, and components
angular.module('myApp', [
  'ngRoute',
  'ngSanitize',
  'myApp.view1',
  'myApp.view2',
  'myApp.version',
  'lumx',
  'ui.gravatar',
  'ngAnimate'
    
]).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.otherwise({redirectTo: '/view1'});
}]);

angular.module('ui.gravatar').config([
  'gravatarServiceProvider', function(gravatarServiceProvider) {
    gravatarServiceProvider.defaults = {
      size     : 100,
      "default": 'http://emailody-stage.herokuapp.com/static/img/avatars/avatar3.png'  // Mystery man as default for missing avatars
    };
}]);

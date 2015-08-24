'use strict';

angular.module('myApp.view1', ['ngRoute'])

.config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/view1', {
        templateUrl: 'static/view1/view1.html',
        controller: 'View1Ctrl'
    });
}])

.controller('View1Ctrl', function ($scope, $http, $sce, $window, LxNotificationService, LxDialogService) {
    // Load all registered users

    $http.get('/v1/gmail/contacts/1').
        success(function(data) {
            $scope.contacts = data['contacts'];
        });
    
    $scope.getMessages = function (jobId) {
		$http.get('/v1/gmail/messages/results/'+jobId).
        success(function(data) {
            $scope.messages = data;
        });
    }
    
    $scope.currentContact = {
        name: false,
        avatar: false
    }

    $scope.currentMessage = {
        subject: '',
        date: '',
        sent: ''
    }
	$scope.rightShow = 'listMails'
    
    $scope.changeRight = function (what) {
        $scope.rightShow = what
    }
	
	
	
    $scope.write = {
        contact: ''
    }

    $scope.urldecode = function (url) {
        return decodeURIComponent(url)
    }

    $scope.getMessage = function (msgId) {
        $http.get('/v1/gmail/message/'+msgId).
        success(function(data) {
            $scope.emailbody = data;
            $sce.trustAsHtml($scope.emailbody);

        });
    }

    $scope.random = function (array) {
        var m = array.length,
            t, i;

        // While there remain elements to shuffle
        while (m) {
            // Pick a remaining element…
            i = Math.floor(Math.random() * m--);

            // And swap it with the current element.
            t = array[m];
            array[m] = array[i];
            array[i] = t;
        }

        return array;
    }


    $scope.opendDialog = function (dialogId) {
        LxDialogService.open(dialogId);
    };

    $scope.closingDialog = function () {
        LxNotificationService.info('Dialog closed!');
    };
    //http://stackoverflow.com/questions/15458609/execute-function-on-page-load
    
    var w = angular.element($window);
    
    w.bind('resize', function () {
		$scope.$apply(function() {
	$scope.stretch();
	console.log('resize');
	})});
    
    $scope.stretch = function () {
        
        console.log('test')
        $scope.scrollbarHeight = w.innerHeight()-100 + 'px'
        
    };
    $scope.stretch();
});

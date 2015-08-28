'use strict';

angular.module('myApp.view1', ['ngRoute', 'base64'])

.config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/view1', {
        templateUrl: 'static/view1/view1.html',
        controller: 'View1Ctrl'
    });
}])


.controller('View1Ctrl', function ($scope, $http, $sce, $window, $timeout, $base64, LxNotificationService, LxDialogService) {
    // Load all registered users



    $scope.mobileBack = function () {
    $scope.leftWrapper = null;
    $scope.rightWrapper = 'hiddenMobile';
    }
    
    $scope.leftWrapper = null
    $scope.rightWrapper = 'hiddenMobile'
    
    $http.get('/v1/gmail/contacts/1').
        success(function(data) {
            $scope.contacts = data['contacts'];
            $http.get('/v1/gmail/listmessages').
                success(function(data) {
                $scope.messageslist = data;
        });
        });
    
    $scope.getMessages = function (id, pagenr, name, address) {
	    $scope.messages = $scope.messageslist[id];
        $scope.rightShow = 'listMails';
        $scope.leftWrapper = 'hiddenMobile';
        $scope.rightWrapper = null;
        $scope.currentContact = {name: name, address: address };
        /*
		$http.get('/v1/gmail/messages/' + id + '/' + pagenr).
        success(function(data) {
            $scope.messages = data;
            $scope.rightShow = 'listMails';
            $scope.leftWrapper = 'hiddenMobile';
            $scope.rightWrapper = null;
            $scope.currentContact = {name: name, address: address };
        }); */
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
        $timeout(function() {
        $scope.rightShow = what
        },150);
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
 var w = angular.element($window);

$scope.stretch = function () {
        
        $scope.scrollbarHeight = w.innerHeight()-$("#contacts").offset().top + 'px'
        
}

$scope.stretch();




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
	})});
    
    
    

});

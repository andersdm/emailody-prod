'use strict';

angular.module('myApp.view1', ['ngRoute', 'base64', 'ngResource'])

.config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/view1', {
        templateUrl: 'static/view1/view1.html',
        controller: 'View1Ctrl'
    });
}])


.controller('View1Ctrl', function ($scope, $http, $resource, $sce, $window, $timeout, $base64, LxNotificationService, LxDialogService) {
    // Load all registered users

    var contacts = $resource("v1/gmail/contacts/:id");
    var messages = $resource("v1/gmail/messages/:id");
    var message = $resource("v1/gmail/message/:id");
    
    contacts.get({
        id: 1
    }).$promise.then(function (data) {
        $scope.contacts = data['contacts']

        $scope.page = {
            dataLoaded: true
        };


        var i
        $scope.messageslist = []
        angular.forEach($scope.contacts, function (value, key) {
            messages.get({
                id: key
            }).$promise.then(function (data) {
                $scope.messageslist[key] = data['messages'];
            }, console.log('test'));

        });
    })
    
    $scope.getMessage = function (msgId) {
        $http.get('/v1/gmail/message/' + msgId).
        success(function (data) {
            $scope.emailbody = $sce.trustAsHtml(data);
            

        })};
    




    $scope.mobileBack = function () {
        $scope.leftWrapper = null;
        $scope.rightWrapper = 'hiddenMobile';
    }

    $scope.leftWrapper = null
    $scope.rightWrapper = 'hiddenMobile'

    /*$http.get('/v1/gmail/contacts/1').
        success(function(data) {
            $scope.contacts = data['contacts'];
        $timeout(function() {
        $scope.page = {dataLoaded: true};
        },1000);
        });
    $http.get('/v1/gmail/listmessages').
                success(function(data) {
                $scope.messageslist = data;
        
                
        });
    */
    $scope.getMessages = function (id, pagenr, name, address) {
        $scope.messages = $scope.messageslist[id];
        $scope.rightShow = 'listMails';
        $scope.leftWrapper = 'hiddenMobile';
        $scope.rightWrapper = null;
        $scope.currentContact = {
            name: name,
            address: address
        };
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
        $timeout(function () {
            $scope.rightShow = what
        }, 150);
    }



    $scope.write = {
        contact: ''
    }

    $scope.urldecode = function (url) {
        return decodeURIComponent(url)
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

        $scope.scrollbarHeight = w.innerHeight() - $("#contacts").offset().top + 'px'

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
        $scope.$apply(function () {
            $scope.stretch();
        })
    });




});
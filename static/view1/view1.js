'use strict';

angular.module('myApp.view1', ['ngRoute', 'base64', 'ngResource'])

.config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/view1', {
        templateUrl: 'static/view1/view1.html',
        controller: 'View1Ctrl'
    });
}])

.controller('View1Ctrl', function ($scope, $http, $resource, $sce, $window, $timeout, $base64, LxNotificationService, LxDialogService) {

    // Load resources

    var contacts = $resource("v1/gmail/contacts/:id");
    var messages = $resource("v1/gmail/messages/:id");
    var message = $resource("v1/gmail/message/:id");

    // Set variables

    var w = angular.element($window);
    $scope.contacts = []
    $scope.rightShow = 'listMails'
    $scope.leftWrapper = null
    $scope.rightWrapper = 'hiddenMobile'
    $scope.currentContact = {
        name: false,
        avatar: false
    }
    $scope.currentMessage = {
        subject: '',
        date: '',
        sent: ''
    }

    $scope.pages = {
        'contactsPage': 1,
        'messagesPage':1
    }

    // Define functions

    $scope.getContacts = function (pageNr) {
        contacts.get({
            id: pageNr
        }).$promise.then(function (data) {
            $scope.contacts = $scope.contacts.concat(data['contacts'])
            console.log($scope.contacts)
            $scope.page = {
                dataLoaded: true
            };
            $scope.stretchLeft();
            $scope.pages['contactsPage'] = $scope.pages['contactsPage'] + 1
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
    }

    $scope.getMessage = function (msgId) {
        $http.get('/v1/gmail/message/' + msgId).
        success(function (data) {
            $scope.emailbody = $sce.trustAsHtml(data);
        })
    };

    $scope.getMessages = function (id, pagenr, name, address, domain) {
        $scope.messages = $scope.messageslist[id];
        $scope.rightShow = 'listMails';
        $scope.currentContact = {
            name: name,
            address: address,
            domain: domain
        };
        $timeout(function () {
            $scope.leftWrapper = 'hiddenMobile';
            $scope.rightWrapper = null;
        }, 150);
        $scope.stretchRight();
    }

    $scope.mobileBack = function () {
        $scope.leftWrapper = null;
        $scope.rightWrapper = 'hiddenMobile';
    }

    $scope.changeRight = function (what) {
        $timeout(function () {
            $scope.rightShow = what
        }, 150);
    }

    $scope.urldecode = function (url) {
        return decodeURIComponent(url)
    }

    $scope.stretchLeft = function () {
        var w = angular.element($window);
        $scope.scrollbarHeightLeft = w.innerHeight() - $("#contacts").offset().top + 'px'
    }

    $scope.stretchRight = function () {
        var w = angular.element($window);
        $scope.scrollbarHeightRight = w.innerHeight() - $("#contacts").offset().top + 'px'
    }

    // Run functions
    $scope.getContacts($scope.pages['contactsPage'])

    //Bind functions
    w.bind('resize', function () {
        $scope.$apply(function () {
            $scope.stretchLeft();
            $scope.stretchRight();
        })
    });




});
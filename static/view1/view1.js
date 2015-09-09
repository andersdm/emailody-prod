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

    $scope.contacts = []
    $scope.pageNr = 1

    $scope.getContacts = function(pageNr) {
    contacts.get({
        id: pageNr
    }).$promise.then(function (data) {
        $scope.contacts = $scope.contacts.concat(data['contacts'])
        console.log($scope.contacts)
        $scope.page = {
            dataLoaded: true

        };
            $scope.stretchLeft();
        $scope.pageNr = $scope.pageNr + 1

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

$scope.getContacts(1)

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
    $scope.getMessages = function (id, pagenr, name, address, initial) {
        $scope.messages = $scope.messageslist[id];
        $scope.rightShow = 'listMails';
        $scope.currentContact = {
            name: name,
            address: address,
            initial: initial
        };
        $timeout(function () {
        $scope.leftWrapper = 'hiddenMobile';
        $scope.rightWrapper = null;


        }, 150);
        /*
		$http.get('/v1/gmail/messages/' + id + '/' + pagenr).
        success(function(data) {
            $scope.messages = data;
            $scope.rightShow = 'listMails';
            $scope.leftWrapper = 'hiddenMobile';
            $scope.rightWrapper = null;
            $scope.currentContact = {name: name, address: address };
        }); */

            $scope.stretchRight();

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


    $scope.switchTheme = function () {
        var color = $scope.theme['themeColor'];

        if ($scope.theme['themeColor'] === 'red') {
            color='blue'
        }
        if ($scope.theme['themeColor'] === 'blue') {
            color='red'
        }

        $scope.theme = {headerColor: 'header-bg-' + color,
                        iconColor: 'icon-color-' + color,
                        themeColor: color
        }
    }

    $scope.setTheme = function (color) {


        $scope.theme = {headerColor: 'header-bg-' + color,
                        iconColor: 'icon-color-' + color,
                        themeColor: color
        }
    }


    $scope.setTheme('blue');

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

    $scope.stretchLeft = function () {

        $scope.scrollbarHeightLeft = w.innerHeight() - $("#contacts").offset().top + 'px'

    }

    $scope.stretchRight = function () {

        $scope.scrollbarHeightRight = w.innerHeight() - $("#contacts").offset().top + 'px'

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
        $scope.$apply(function () {
            $scope.stretchLeft();
            $scope.stretchRight();
        })
    });




});

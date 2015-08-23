'use strict';

angular.module('myApp.view1', ['ngRoute'])

.config(['$routeProvider', function ($routeProvider) {
    $routeProvider.when('/view1', {
        templateUrl: 'static/view1/view1.html',
        controller: 'View1Ctrl'
    });
}])

.controller('View1Ctrl', function ($scope, $http, $sce, LxNotificationService, LxDialogService) {
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

    $scope.modal = function (what) {
        $scope.modalShow = what
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

    /*$scope.chats = [
        {
            subject: 'Confuse my cat',
            snippet: 'I love cheese, especially airedale queso. Cheese and biscuits halloumi...',
            date: 'May 1. 2015',
            sent: '',
            read: 'true'
        },

        {
            subject: 'My hovercraft is full of eels.',
            snippet: 'Zombie ipsum reversus ab viral inferno, nam rick grimes malum cerebro...',
            date: 'May 1. 2015',
            sent: 'true',
            read: 'true'
        },
        {
            subject: 'If I said you had a beautiful body',
            snippet: 'Zombie ipsum reversus ab viral inferno, nam rick grimes malum cerebro...',
            date: 'May 1. 2015',
            sent: '',
            read: 'true'
        },

        {
            subject: 'Would you hold it against me',
            snippet: 'Scratch the furniture spit up on light gray carpet instead of adjacent...',
            date: 'May 1. 2015',
            sent: '',
            read: 'true'
        },
        {
            subject: 'I am no longer infected',
            snippet: 'Webtwo ipsum dolor sit amet, eskobo chumby doostang bebo...',
            date: 'May 1. 2015',
            sent: 'true',
            read: 'true'
        },
        {
            subject: 'This is Monty Pythons flying circus',
            snippet: "Lebowski ipsum yeah? What do you think happens when you get rad?...",
            date: 'May 1. 2015',
            sent: 'true',
            read: 'true'
        }

    ];

    /*$scope.mails = [
        {
            name: 'Camilla Kær Mørkholt',
            avatar: 'img/Camilla.jpg',
            snippet: 'I love cheese, especially airedale queso. Cheese and biscuits halloumi...',
            date: '11:02 PM'
      },
        {
            name: 'Julie Seabrook',
            avatar: 'img/Julie.jpg',
            snippet: 'Zombie ipsum reversus ab viral inferno, nam rick grimes malum cerebro...',
            date: '11:01 PM'
      },
        {
            name: 'Gener Delosreyes',
            avatar: '',
            snippet: "Raw denim pour-over readymade Etsy Pitchfork. Four dollar toast pickled...",
            date: '11:00 PM'
      },
        {
            name: 'Facebook',
            avatar: 'img/Facebook.png',
            snippet: 'Scratch the furniture spit up on light gray carpet instead of adjacent...',
            date: '10:59 PM'
      },
        {
            name: 'Magnus Ohrt Nissen',
            avatar: 'img/Magnus.jpg',
            snippet: 'Webtwo ipsum dolor sit amet, eskobo chumby doostang bebo...',
            date: '10:58 PM'
        },
        {
            name: 'Gani Ferrer',
            avatar: '',
            snippet: "Lebowski ipsum yeah? What do you think happens when you get rad?...",
            date: '10:57 PM'
      },
        {
            name: 'Maja Damsgaard Mikkelsen',
            avatar: 'img/Maja.jpg',
            snippet: 'Zombie ipsum reversus ab viral inferno, nam rick grimes malum cerebro...',
            date: '10:56 PM'
      },
        {
            name: 'Gener Delosreyes',
            avatar: '',
            snippet: "Raw denim pour-over readymade Etsy Pitchfork. Four dollar toast...",
            date: '10:55 PM'
      },
        {
            name: 'Lawrence Ray',
            avatar: '',
            snippet: 'Scratch the furniture spit up on light gray carpet instead of...',
            date: '10:54 PM'
      },
        {
            name: 'Magnus Ohrt Nissen',
            avatar: '',
            snippet: 'Webtwo ipsum dolor sit amet, eskobo chumby doostang bebo...',
            date: '10:53 PM'
        },
        {
            name: 'Sebastian Bue Rakov',
            avatar: 'img/Sebastian.jpg',
            snippet: "Lebowski ipsum yeah? What do you think happens when you get rad?...",
            date: '10:52 PM'
      }
    ];*/



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
    var stretch = function () {
        $('.stretch').css({
            height: $(window).innerHeight() + 565
        });
    };
    stretch();
});

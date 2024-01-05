window.onscroll = function() {navChangeColor()};

document.querySelector('.my-nav').classList.add("fixed-top")
function navChangeColor() {
    var nav = document.querySelector('nav');
    var btnBook = nav.querySelector('.btn-on-nav');
    var logo = nav.querySelector('.navbar-brand').querySelector('img')

    if (window.pageYOffset >= 100) {
        nav.classList.add("bg-white", "shadow-sm")
        nav.classList.remove("bg-nav", "navbar-dark")
        btnBook.classList.remove("text-white")
//        logo.src = "static/src/logo_black.png"
    }
    else {
        nav.classList.remove("bg-white", "shadow-sm")
        nav.classList.add("bg-nav", "navbar-dark")
        btnBook.classList.add("text-white")
//        logo.src = "static/src/logo.png"
    }
}

$('.message a').click(function(){
   $('form').animate({height: "toggle", opacity: "toggle"}, "slow");
});
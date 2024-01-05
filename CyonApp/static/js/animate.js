window.onload = function(){
    wow = new WOW({
          boxClass:     'wow',
          animateClass: 'animate__animated',
          offset:       0,
          mobile:       true,
          live:         true
          })
    wow.init();
}
document.documentElement.style.setProperty('--animate-duration', '2s');
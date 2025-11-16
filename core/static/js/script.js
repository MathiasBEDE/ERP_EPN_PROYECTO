document.addEventListener('DOMContentLoaded', function() {
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');
    
    function toggleUserMenu() {
        if (userMenu) {
            userMenu.classList.toggle('show');
        }
    }
    
    if (userMenuButton) {
        userMenuButton.addEventListener('click', function(event) {
            event.stopPropagation();
            toggleUserMenu();
        });
    }
    
    document.addEventListener('click', function(event) {
        if (userMenu && userMenuButton) {
            if (!userMenuButton.contains(event.target) && !userMenu.contains(event.target)) {
                userMenu.classList.remove('show');
            }
        }
    });
});










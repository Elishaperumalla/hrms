document.addEventListener("DOMContentLoaded", function () {

    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarClose = document.getElementById("sidebarClose");
    const sidebarOverlay = document.getElementById("sidebarOverlay");


    // OPEN SIDEBAR
    if (sidebarToggle) {

        sidebarToggle.addEventListener("click", function () {

            sidebar.classList.add("show");

            if (sidebarOverlay) {
                sidebarOverlay.classList.add("show");
            }

        });

    }


    // CLOSE SIDEBAR
    if (sidebarClose) {

        sidebarClose.addEventListener("click", function () {

            sidebar.classList.remove("show");

            if (sidebarOverlay) {
                sidebarOverlay.classList.remove("show");
            }

        });

    }


    // CLOSE WHEN CLICKING OUTSIDE
    if (sidebarOverlay) {

        sidebarOverlay.addEventListener("click", function () {

            sidebar.classList.remove("show");

            sidebarOverlay.classList.remove("show");

        });

    }


    // CLOSE SIDEBAR AFTER CLICKING A MENU ITEM ON MOBILE
    const sidebarLinks = document.querySelectorAll(".sidebar-link");

    sidebarLinks.forEach(function (link) {

        link.addEventListener("click", function () {

            if (window.innerWidth <= 991) {

                sidebar.classList.remove("show");

                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove("show");
                }

            }

        });

    });

});
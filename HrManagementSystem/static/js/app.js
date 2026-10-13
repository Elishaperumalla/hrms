// document.addEventListener("DOMContentLoaded", function () {

//     const sidebar = document.getElementById("sidebar");
//     const sidebarToggle = document.getElementById("sidebarToggle");
//     const sidebarClose = document.getElementById("sidebarClose");
//     const sidebarOverlay = document.getElementById("sidebarOverlay");


//     // OPEN SIDEBAR
//     if (sidebarToggle) {

//         sidebarToggle.addEventListener("click", function () {

//             sidebar.classList.add("show");

//             if (sidebarOverlay) {
//                 sidebarOverlay.classList.add("show");
//             }

//         });

//     }


//     // CLOSE SIDEBAR
//     if (sidebarClose) {

//         sidebarClose.addEventListener("click", function () {

//             sidebar.classList.remove("show");

//             if (sidebarOverlay) {
//                 sidebarOverlay.classList.remove("show");
//             }

//         });

//     }


//     // CLOSE WHEN CLICKING OUTSIDE
//     if (sidebarOverlay) {

//         sidebarOverlay.addEventListener("click", function () {

//             sidebar.classList.remove("show");

//             sidebarOverlay.classList.remove("show");

//         });

//     }


//     // CLOSE SIDEBAR AFTER CLICKING A MENU ITEM ON MOBILE
//     const sidebarLinks = document.querySelectorAll(".sidebar-link");

//     sidebarLinks.forEach(function (link) {

//         link.addEventListener("click", function () {

//             if (window.innerWidth <= 991) {

//                 sidebar.classList.remove("show");

//                 if (sidebarOverlay) {
//                     sidebarOverlay.classList.remove("show");
//                 }

//             }

//         });

//     });

// });
document.addEventListener("DOMContentLoaded", function () {

    /*
    ============================================================
    SIDEBAR
    ============================================================
    */

    const sidebar =
        document.getElementById("sidebar");

    const sidebarToggle =
        document.getElementById("sidebarToggle");

    const sidebarClose =
        document.getElementById("sidebarClose");

    const sidebarOverlay =
        document.getElementById("sidebarOverlay");


    /*
    OPEN SIDEBAR
    */

    if (sidebarToggle && sidebar) {

        sidebarToggle.addEventListener(
            "click",
            function () {

                sidebar.classList.add("show");

                if (sidebarOverlay) {

                    sidebarOverlay.classList.add("show");

                }

            }
        );

    }


    /*
    CLOSE SIDEBAR
    */

    if (sidebarClose && sidebar) {

        sidebarClose.addEventListener(
            "click",
            function () {

                sidebar.classList.remove("show");

                if (sidebarOverlay) {

                    sidebarOverlay.classList.remove("show");

                }

            }
        );

    }


    /*
    CLOSE USING OVERLAY
    */

    if (sidebarOverlay && sidebar) {

        sidebarOverlay.addEventListener(
            "click",
            function () {

                sidebar.classList.remove("show");

                sidebarOverlay.classList.remove("show");

            }
        );

    }


    /*
    CLOSE SIDEBAR AFTER MENU CLICK
    */

    const sidebarLinks =
        document.querySelectorAll(
            ".sidebar-link"
        );


    sidebarLinks.forEach(function (link) {

        link.addEventListener(
            "click",
            function () {

                if (
                    window.innerWidth <= 991 &&
                    sidebar
                ) {

                    sidebar.classList.remove(
                        "show"
                    );


                    if (sidebarOverlay) {

                        sidebarOverlay.classList.remove(
                            "show"
                        );

                    }

                }

            }
        );

    });



    /*
    ============================================================
    HRMS THEME SYSTEM
    ============================================================
    */


    const root =
        document.documentElement;


    const themeToggle =
        document.getElementById(
            "themeToggle"
        );


    const themeToggleIcon =
        document.getElementById(
            "themeToggleIcon"
        );


    const themeLightButton =
        document.getElementById(
            "themeLight"
        );


    const themeDarkButton =
        document.getElementById(
            "themeDark"
        );


    const themeSystemButton =
        document.getElementById(
            "themeSystem"
        );


    const THEME_KEY =
        "hrms-theme";



    /*
    ============================================================
    GET SYSTEM THEME
    ============================================================
    */

    function getSystemTheme() {

        const mediaQuery =
            window.matchMedia(
                "(prefers-color-scheme: dark)"
            );


        if (mediaQuery.matches) {

            return "dark";

        }


        return "light";

    }



    /*
    ============================================================
    GET SAVED THEME
    ============================================================
    */

    function getSavedTheme() {

        const savedTheme =
            localStorage.getItem(
                THEME_KEY
            );


        if (
            savedTheme === "light" ||
            savedTheme === "dark" ||
            savedTheme === "system"
        ) {

            return savedTheme;

        }


        return "light";

    }



    /*
    ============================================================
    SET ROOT THEME
    ============================================================
    */

    function setRootTheme(actualTheme) {

        root.classList.remove(
            "theme-light",
            "theme-dark"
        );


        if (actualTheme === "dark") {

            root.classList.add(
                "theme-dark"
            );

        }

        else {

            root.classList.add(
                "theme-light"
            );

        }

    }



    /*
    ============================================================
    UPDATE NAVBAR BUTTON
    ============================================================
    */

    function updateNavbarButton(
        actualTheme
    ) {

        if (!themeToggle) {

            return;

        }


        if (actualTheme === "dark") {

            if (themeToggleIcon) {

                themeToggleIcon.className =
                    "bi bi-sun-fill";

            }


            themeToggle.setAttribute(
                "aria-label",
                "Switch to light mode"
            );


            themeToggle.setAttribute(
                "title",
                "Switch to light mode"
            );

        }

        else {

            if (themeToggleIcon) {

                themeToggleIcon.className =
                    "bi bi-moon-fill";

            }


            themeToggle.setAttribute(
                "aria-label",
                "Switch to dark mode"
            );


            themeToggle.setAttribute(
                "title",
                "Switch to dark mode"
            );

        }

    }



    /*
    ============================================================
    UPDATE SETTINGS BUTTONS
    ============================================================
    */

    function updateSettingsButtons(
        selectedTheme
    ) {

        const buttons = [

            themeLightButton,

            themeDarkButton,

            themeSystemButton

        ];


        buttons.forEach(
            function (button) {

                if (button) {

                    button.classList.remove(
                        "theme-option-active"
                    );

                }

            }
        );


        if (
            selectedTheme === "light" &&
            themeLightButton
        ) {

            themeLightButton.classList.add(
                "theme-option-active"
            );

        }


        if (
            selectedTheme === "dark" &&
            themeDarkButton
        ) {

            themeDarkButton.classList.add(
                "theme-option-active"
            );

        }


        if (
            selectedTheme === "system" &&
            themeSystemButton
        ) {

            themeSystemButton.classList.add(
                "theme-option-active"
            );

        }

    }



    /*
    ============================================================
    APPLY THEME
    ============================================================
    */

    function applyTheme(
        selectedTheme,
        savePreference = true
    ) {

        let actualTheme =
            selectedTheme;


        /*
        SYSTEM MODE
        */

        if (
            selectedTheme === "system"
        ) {

            actualTheme =
                getSystemTheme();

        }


        /*
        SAFETY
        */

        if (
            actualTheme !== "dark" &&
            actualTheme !== "light"
        ) {

            actualTheme = "light";

        }


        /*
        APPLY HTML CLASS
        */

        setRootTheme(
            actualTheme
        );


        /*
        SAVE PREFERENCE
        */

        if (savePreference) {

            localStorage.setItem(
                THEME_KEY,
                selectedTheme
            );

        }


        /*
        UPDATE NAVBAR
        */

        updateNavbarButton(
            actualTheme
        );


        /*
        UPDATE SETTINGS
        */

        updateSettingsButtons(
            selectedTheme
        );

    }



    /*
    ============================================================
    NAVBAR TOGGLE
    ============================================================
    */

    if (themeToggle) {

        themeToggle.addEventListener(
            "click",
            function () {

                const currentActualTheme =
                    root.classList.contains(
                        "theme-dark"
                    )
                        ? "dark"
                        : "light";


                if (
                    currentActualTheme === "dark"
                ) {

                    applyTheme(
                        "light"
                    );

                }

                else {

                    applyTheme(
                        "dark"
                    );

                }

            }
        );

    }



    /*
    ============================================================
    SETTINGS - LIGHT
    ============================================================
    */

    if (themeLightButton) {

        themeLightButton.addEventListener(
            "click",
            function () {

                applyTheme(
                    "light"
                );

            }
        );

    }



    /*
    ============================================================
    SETTINGS - DARK
    ============================================================
    */

    if (themeDarkButton) {

        themeDarkButton.addEventListener(
            "click",
            function () {

                applyTheme(
                    "dark"
                );

            }
        );

    }



    /*
    ============================================================
    SETTINGS - SYSTEM
    ============================================================
    */

    if (themeSystemButton) {

        themeSystemButton.addEventListener(
            "click",
            function () {

                applyTheme(
                    "system"
                );

            }
        );

    }



    /*
    ============================================================
    INITIALIZE THEME
    ============================================================
    */

    const savedTheme =
        getSavedTheme();


    applyTheme(
        savedTheme,
        false
    );



    /*
    ============================================================
    FOLLOW SYSTEM THEME
    ============================================================
    */

    const systemMediaQuery =
        window.matchMedia(
            "(prefers-color-scheme: dark)"
        );


    function handleSystemThemeChange() {

        const selectedTheme =
            getSavedTheme();


        if (
            selectedTheme === "system"
        ) {

            applyTheme(
                "system",
                false
            );

        }

    }


    if (
        systemMediaQuery.addEventListener
    ) {

        systemMediaQuery.addEventListener(
            "change",
            handleSystemThemeChange
        );

    }

    else if (
        systemMediaQuery.addListener
    ) {

        systemMediaQuery.addListener(
            handleSystemThemeChange
        );

    }

});
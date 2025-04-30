function windowScroll() {
    var e = document.getElementById("navbar-custom");
    if (e) {
        if (document.body.scrollTop >= 50 || document.documentElement.scrollTop >= 50) {
            e.classList.add("nav-sticky");
        } else {
            e.classList.remove("nav-sticky");
        }
    }
}

feather.replace();
window.addEventListener("scroll", function(e) {
    e.preventDefault();
    windowScroll();
});

var triggerTabList = [].slice.call(document.querySelectorAll("#tab-menu a"));
var collapses = document.querySelectorAll(".navbar-nav .collapse");

triggerTabList.forEach(function (e) {
    var t = new bootstrap.Tab(e);
    e.addEventListener("click", function (e) {
        e.preventDefault();
        t.show();
        document.body.classList.remove("enlarge-menu");
    });
});

collapses.forEach(function(t) {
    var a = new bootstrap.Collapse(t, {toggle: false});
    t.addEventListener("show.bs.collapse", function (e) {
        e.stopPropagation();
        var parentCollapse = t.parentElement.closest(".collapse");
        if (parentCollapse) {
            parentCollapse.querySelectorAll(".collapse").forEach(function (collapseEl) {
                var instance = bootstrap.Collapse.getInstance(collapseEl);
                if (instance !== a) {
                    instance.hide();
                }
            });
        }
    });
    t.addEventListener("hide.bs.collapse", function (e) {
        e.stopPropagation();
        t.querySelectorAll(".collapse").forEach(function (collapseEl) {
            bootstrap.Collapse.getInstance(collapseEl).hide();
        });
    });
});

try {
    var togglemenu = document.getElementById("togglemenu");
    if (togglemenu) {
        togglemenu.addEventListener("click", function (e) {
            e.preventDefault();
            document.body.classList.toggle("enlarge-menu");
        });
    }
} catch (e) {}

var bodyElement = document.getElementsByTagName("body")[0];
if (window.screen.width < 1025) {
    bodyElement.classList.add("enlarge-menu", "enlarge-menu-all");
} else if (window.screen.width < 1340) {
    bodyElement.classList.remove("enlarge-menu-all");
    bodyElement.classList.add("enlarge-menu");
}

window.addEventListener("resize", function () {
    if (window.screen.width < 1025) {
        bodyElement.classList.add("enlarge-menu", "enlarge-menu-all");
    } else if (window.screen.width < 1340) {
        bodyElement.classList.remove("enlarge-menu-all");
        bodyElement.classList.add("enlarge-menu");
    }
});

document.querySelectorAll(".leftbar-tab-menu a").forEach(function (e) {
    var currentUrl = window.location.href.split(/[?#]/)[0];
    if (e.href === currentUrl) {
        e.classList.add("active");
        if (!e.parentElement.parentElement.classList.contains("navbar-nav")) {
            var o = e.closest(".collapse");
            if (o) {
                o.classList.add("show");
                var a = o.parentElement.querySelector("a");
                if (a) {
                    a.classList.remove("collapsed");
                    a.setAttribute("aria-expanded", "true");
                }
                var parentCollapse = o.parentElement.closest(".collapse");
                if (parentCollapse) {
                    parentCollapse.classList.add("show");
                    var aParent = parentCollapse.parentElement.querySelector("a");
                    if (aParent) {
                        aParent.classList.remove("collapsed");
                        aParent.setAttribute("aria-expanded", "true");
                    }
                    parentCollapse.parentElement.childNodes[1].setAttribute("aria-expanded", "true");
                }
            }
            var n = e.closest(".tab-pane");
            if (n) {
                n.classList.add("active");
                document.querySelectorAll("a").forEach(function (aE) {
                    if (aE.href.includes(n.id)) {
                        aE.classList.add("active");
                    }
                });
            }
        }
    }
});

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
var tooltipList = tooltipTriggerList.map(function (e) {
    return new bootstrap.Tooltip(e);
});

var dropdowns = document.querySelectorAll(".dropup, .dropend, .dropdown, .dropstart");
var events = ["click"];

function toggleDropdown(e, t) {
    var n = t.closest(".dropdown-menu");
    if (n) {
        e.preventDefault();
        e.stopPropagation();
        var a = t.querySelector(".dropdown-menu");
        var dropdownMenus = n.querySelectorAll(".dropdown-menu");
        dropdownMenus.forEach(function (dropdownEl) {
            if (dropdownEl !== a) {
                dropdownEl.classList.remove("show");
            }
        });
        a.classList.add("show");
    }
}

function hideDropdowns(e) {
    var nestedMenus = e.querySelectorAll(".dropdown-menu .dropdown-menu");
    if (nestedMenus) {
        nestedMenus.forEach(function (dropdownEl) {
            dropdownEl.classList.remove("show");
        });
    }
}

function toggleMenu() {
    var mobileToggle = document.getElementById("mobileToggle");
    if (mobileToggle) {
        mobileToggle.classList.toggle("open");
    }
    var navigation = document.getElementById("navigation");
    if (navigation) {
        if (navigation.style.display === "block") {
            navigation.style.display = "none";
        } else {
            navigation.style.display = "block";
        }
    }
}

function activateMenu() {
    var subMenuItems = document.getElementsByClassName("sub-menu-item");
    if (subMenuItems) {
        var activeItem = null;
        for (var o = 0; o < subMenuItems.length; o++) {
            if (subMenuItems[o].href === window.location.href) {
                activeItem = subMenuItems[o];
                break;
            }
        }
        if (activeItem) {
            activeItem.classList.add("active");
            var li = getClosest(activeItem, "li");
            if (li) li.classList.add("active");
            var parentMenuItem = getClosest(activeItem, ".parent-menu-item");
            if (parentMenuItem) {
                parentMenuItem.classList.add("active");
                var menuItem = parentMenuItem.querySelector(".menu-item");
                if (menuItem) menuItem.classList.add("active");
                var parentParentMenuItem = getClosest(parentMenuItem, ".parent-parent-menu-item");
                if (parentParentMenuItem) parentParentMenuItem.classList.add("active");
            } else {
                var parentParentMenuItemAlt = getClosest(activeItem, ".parent-parent-menu-item");
                if (parentParentMenuItemAlt) parentParentMenuItemAlt.classList.add("active");
            }
        }
    }
}

function getClosest(element, selector) {
    while (element && element !== document) {
        if (element.matches(selector)) {
            return element;
        }
        element = element.parentNode;
    }
    return null;
}

dropdowns.forEach(function (t) {
    var e = t.querySelector('[data-bs-toggle="dropdown"]');
    if (e) {
        e.addEventListener(events[0], function (e) {
            toggleDropdown(e, t);
        });
    } else {
        hideDropdowns(t);
    }
});

document.querySelectorAll(".menu-body a").forEach(function (e) {
    var currentUrl = window.location.href.split(/[?#]/)[0];
    if (e.href === currentUrl) {
        e.classList.add("active");
        e.parentNode.classList.add("menuitem-active");
        var navLink = e.parentNode.querySelector(".nav-link");
        if (navLink) {
            navLink.setAttribute("aria-expanded", "true");
        }
        e.parentNode.parentNode.classList.add("show");
        var parentNavLink = e.parentNode.parentNode.parentElement.querySelector(".nav-link");
        if (parentNavLink) {
            parentNavLink.classList.add("active");
        }
    }
});

document.querySelectorAll("#navigation li a").forEach(function (e) {
    var currentUrl = window.location.href.split(/[?#]/)[0];
    if (e.href === currentUrl) {
        e.classList.add("active");
        var ariaLabelledBy = e.getAttribute("aria-labelledby");
        while (ariaLabelledBy) {
            var relatedElement = document.querySelector("#" + ariaLabelledBy);
            if (relatedElement) {
                relatedElement.classList.add("active");
                relatedElement.setAttribute("aria-expanded", "true");
                ariaLabelledBy = relatedElement.getAttribute("aria-labelledby");
            } else {
                break;
            }
        }
        e.parentNode.parentNode.classList.add("active");
        var navLink = e.parentNode.parentNode.parentElement.querySelector(".nav-link");
        if (navLink) {
            navLink.classList.add("active");
        }
        e.parentNode.parentNode.parentNode.parentNode.classList.add("active");
        e.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.classList.add("active");
    }
});

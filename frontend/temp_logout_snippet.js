        // ==========================================
        // LOGOUT FUNCTION
        // ==========================================
        function logout() {
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = 'login.html';
        }

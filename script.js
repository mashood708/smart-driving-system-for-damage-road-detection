$(document).ready(function() {
    // Function to confirm user deletion
    function confirmDelete() {
        return confirm("Are you sure you want to delete this user?");
    }

    // Event listener for start button
    $("#startBtn").click(function() {
        $.ajax({
            url: "/start_detection",
            success: function(data) {
                alert(data);
            },
            error: function(xhr, status, error) {
                console.error("Error:", error);
            }
        });
    });

    // Event listener for stop button
    $("#stopBtn").click(function() {
        $.ajax({
            url: "/stop_detection",
            success: function(data) {
                alert(data);
            },
            error: function(xhr, status, error) {
                console.error("Error:", error);
            }
        });
    });

    // Function to validate the create user form
    function validateCreateUserForm() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const role = document.getElementById('role_id').value.trim();

        if (username === '' || password === '' || role === '') {
            alert("All fields are required");
            return false;
        }

        return true;
    }

    // Function to validate the edit user form
    function validateEditUserForm() {
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const role = document.getElementById('role_id').value.trim();

        if (username === '' || password === '' || role === '') {
            alert("All fields are required");
            return false;
        }

        return true;
    }
});

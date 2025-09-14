document.addEventListener("DOMContentLoaded", () => {

  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const user = document.getElementById("loginUser").value;
      const pass = document.getElementById("loginPass").value;

      if (user === "admin" && pass === "admin") {
        localStorage.setItem("loggedIn", "true");
        window.location.href = "dashboard.html";
      } else {
        document.getElementById("loginError").innerText = "Invalid credentials!";
      }
    });
  }


  const signupForm = document.getElementById("signupForm");
  if (signupForm) {
    signupForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const user = document.getElementById("signupUser").value;
      document.getElementById("signupMsg").innerText =
        `Account for "${user}" created (demo only).`;
    });
  }


  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("loggedIn");
      window.location.href = "login.html";
    });
  }

 
  if (window.location.pathname.endsWith("dashboard.html")) {
    if (localStorage.getItem("loggedIn") !== "true") {
      window.location.href = "login.html";
    }
  }


  if (document.getElementById("performanceChart")) {
    const ctx = document.getElementById("performanceChart").getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: ["Jan", "Feb", "Mar", "Apr", "May"],
        datasets: [{
          label: "Performance",
          data: [10, 20, 15, 30, 25],
          borderColor: "blue",
          backgroundColor: "rgba(0,123,255,0.2)"
        }]
      }
    });
  }
});

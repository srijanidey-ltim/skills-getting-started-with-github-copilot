document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        // Create activity card
        const card = document.createElement("div");
        card.className = "activity-card";

        const participantsList =
          details.participants.length > 0
            ? details.participants.map((p) => `<li><span>${p}</span><button class="delete-btn" data-activity="${name}" data-email="${p}" title="Unregister participant">✕</button></li>`).join("")
            : '<p class="no-participants">No participants yet</p>';

        card.innerHTML = `
          <h4>${name}</h4>
          <p><strong>Description:</strong> ${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Max Participants:</strong> ${details.max_participants}</p>
          <div class="participants-section">
            <h5>Signed Up (${details.participants.length})</h5>
            ${details.participants.length > 0 
              ? `<ul class="participants-list">${participantsList}</ul>`
              : participantsList
            }
          </div>
        `;

        activitiesList.appendChild(card);

        // Add delete button event listeners
        const deleteButtons = card.querySelectorAll(".delete-btn");
        deleteButtons.forEach((btn) => {
          btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const activity = btn.dataset.activity;
            const email = btn.dataset.email;

            if (confirm(`Unregister ${email} from ${activity}?`)) {
              try {
                const response = await fetch(
                  `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
                  {
                    method: "DELETE",
                  }
                );

                if (response.ok) {
                  messageDiv.textContent = `${email} unregistered from ${activity}`;
                  messageDiv.className = "success";
                  messageDiv.classList.remove("hidden");
                  fetchActivities();

                  setTimeout(() => {
                    messageDiv.classList.add("hidden");
                  }, 5000);
                } else {
                  const result = await response.json();
                  messageDiv.textContent = result.detail || "Failed to unregister";
                  messageDiv.className = "error";
                  messageDiv.classList.remove("hidden");
                }
              } catch (error) {
                messageDiv.textContent = "Failed to unregister. Please try again.";
                messageDiv.className = "error";
                messageDiv.classList.remove("hidden");
                console.error("Error unregistering:", error);
              }
            }
          });
        });

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});

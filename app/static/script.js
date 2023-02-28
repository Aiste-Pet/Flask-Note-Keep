function showInput(select) {
  if (select.value == "Create new..") {
    document.getElementById("inputDiv").style.display = "block";
    document.getElementById("form12").removeAttribute("disabled");
    document.getElementById("form12").style.display = "inline-block";
  } else {
    document.getElementById("inputLabel").style.display = "inline-block";
    document.getElementById("inputDiv").style.display = "none";
    document.getElementById("form12").setAttribute("disabled", "");
    document.getElementById("form12").style.display = "none";
  }
}

function editCategory(categoryId, categoryName) {
  const row = document.getElementById("category-" + categoryId);
  const nameCell = row.getElementsByTagName("td")[0];
  const input = document.createElement("input");
  input.type = "text";
  input.name = "name";
  input.id = "edit-category-input";
  input.value = categoryName;
  nameCell.innerHTML = "";
  nameCell.appendChild(input);
  const saveButton = document.createElement("button");
  saveButton.type = "submit";
  saveButton.className = "btn btn-primary";
  saveButton.innerText = "Save";
  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "btn btn-secondary";
  cancelButton.innerText = "Cancel";
  const actionsCell = row.getElementsByTagName("td")[1];
  actionsCell.innerHTML = "";
  actionsCell.appendChild(saveButton);
  actionsCell.appendChild(cancelButton);

  cancelButton.addEventListener("click", function () {
    nameCell.innerHTML = categoryName;
    actionsCell.innerHTML =
      '<form method="POST" action="/delete_category/' +
      categoryId +
      '">' +
      "</form>" +
      '<button type="button" class="btn btn-primary" onclick="editCategory(' +
      categoryId +
      ", '" +
      categoryName +
      "')\">Edit</button>" +
      '<button type="submit" class="btn btn-danger">Delete</button>';
  });

  saveButton.addEventListener("click", function () {
    const categoryName = document.getElementById("edit-category-input").value;
    $.ajax({
      url: "edit_category/" + categoryId,
      type: "POST",
      data: {
        name: categoryName,
      },
      success: function (response) {
        if (response.success) {
          // The category was successfully edited, show a success flash message
          flashMessage("success", response.message);
          // Reload the page to show the updated category
          window.location.reload();
        } else {
          // The category name is invalid or already exists, show an error flash message
          flashMessage("error", response.message);
        }
      },
      error: function (xhr) {
        flashMessage("error", "An error occurred while editing the category");
      },
    });
  });
}

function flashMessage(type, message) {
  const flashMessages = document.getElementById("flash-messages");
  const alertClass = type === "error" ? "alert-danger" : "alert-success";
  const flashMessage = `
    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
      ${message}
    </div>
  `;
  flashMessages.innerHTML += flashMessage;
}

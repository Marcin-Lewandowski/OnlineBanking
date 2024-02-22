function updateRecipientDetails() {
    console.log("Funkcja updateRecipientDetails została wywołana.");
    var recipientSelect = document.getElementById('saved_recipient');
    var selectedOption = recipientSelect.options[recipientSelect.selectedIndex];
    var sortCode = selectedOption.getAttribute('data-sort-code');
    var accountNumber = selectedOption.getAttribute('data-account-number');

    document.getElementById('recipient_sort_code').value = sortCode ? sortCode : '';
    document.getElementById('recipient_account_number').value = accountNumber ? accountNumber : '';
}


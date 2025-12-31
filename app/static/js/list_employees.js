document.addEventListener('htmx:confirm', function (event) {
    // Prevent the default browser confirmation dialog
    if (!event.detail.question) return

    event.preventDefault();

    // The confirmation message can be accessed from the hx-confirm attribute value
    const confirmMessage = event.detail.question || "Deseja excluir este funcionário?(O usuário associado ao funcionario será deletado.)";

    Swal.fire({
        title: 'Confirmação de Exclusão',
        text: confirmMessage,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sim, prosseguir!'
    }).then((result) => {
        if (result.isConfirmed) {
            // If the user confirms, issue the original htmx request
            event.detail.issueRequest(true);
        }
    });
});
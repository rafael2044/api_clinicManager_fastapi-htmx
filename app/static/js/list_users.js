// Escuta o evento enviado pelo servidor para fechar o modal após sucesso
document.body.addEventListener('closeModal', function() {
    const modal = document.getElementById('modal-container');
    if (modal) modal.remove();
    alert('Senha atualizada com sucesso!');
});
(function () {
        if (typeof IMask !== "undefined") {
            const inputCpf = document.getElementById("input-cpf");
            const maskCpf = {
                mask: "000.000.000-00",
            };
            IMask(inputCpf, maskCpf);
        }
    })();
    // Script simples para simular o comportamento de abas (estilo do botão)
document.body.addEventListener('htmx:afterOnLoad', function(evt) {
    // Verifica se o alvo da troca foi a seção dinâmica do formulário
    if (evt.detail.target.id === 'dynamic-form-section') {
        const isDoc = evt.detail.xhr.responseURL.includes('role=doctor');
        const btnDoc = document.getElementById('btn-doctor');
        const btnAdm = document.getElementById('btn-admin');
        const submitBtn = document.getElementById('submit-btn');

        if (isDoc) {
            // Estilo para o botão Médico Ativo
            btnDoc.classList.add('btn-white', 'shadow-sm', 'text-primary');
            btnDoc.classList.remove('text-secondary');
            
            // Estilo para o botão Admin Inativo
            btnAdm.classList.add('text-secondary');
            btnAdm.classList.remove('btn-white', 'shadow-sm', 'text-primary');
            
            // Cor do botão de submit (Azul para médicos)
            submitBtn.classList.remove('btn-info'); // Classe caso estivesse em admin
            submitBtn.classList.add('btn-primary');
        } else {
            // Estilo para o botão Admin Ativo
            btnAdm.classList.add('btn-white', 'shadow-sm', 'text-primary');
            btnAdm.classList.remove('text-secondary');
            
            // Estilo para o botão Médico Inativo
            btnDoc.classList.add('text-secondary');
            btnDoc.classList.remove('btn-white', 'shadow-sm', 'text-primary');
            
            // Cor do botão de submit (Ciano/Info para administrativo)
            submitBtn.classList.remove('btn-primary');
            submitBtn.classList.add('btn-info');
            submitBtn.classList.add('text-white'); // Garante leitura no botão info
        }
    }
});
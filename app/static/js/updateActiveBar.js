function updateActiveNav() {
    const currentPath = window.location.pathname;
    console.log(currentPath);

    document
        .querySelectorAll("nav button[hx-get]")
        .forEach((btn) => {
            const btnPath = btn.getAttribute("hx-get");
            console.log(btnPath.split("/"));
            // Verifica se a URL atual começa com o caminho do botão
            // Ex: se a URL é /patients/edit/1, o botão de /patients/list deve brilhar
            if (
                btnPath.length > 1 &&
                currentPath.startsWith(btnPath.split("/")[1], 1)
            ) {
                btn.classList.add(
                    "bg-blue-800",
                    "ring-2",
                    "ring-white",
                );
            } else {
                btn.classList.remove(
                    "bg-blue-800",
                    "ring-2",
                    "ring-white",
                );
            }
        });
}

// Executa sempre que o HTMX terminar de trocar o conteúdo e atualizar a URL
document.body.addEventListener("htmx:afterOnLoad", updateActiveNav);

// Executa ao carregar a página pela primeira vez (F5)
window.addEventListener("load", updateActiveNav);
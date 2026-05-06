function descargarPDF(facturaId) {
    const element = document.querySelector('.invoice-container');
    
    // Configuración optimizada para asegurar que se vea TODO
    const opt = {
        margin:       [0, 0, 0, 0], // Sin margenes externos para aprovechar el diseño
        filename:     `Factura_HotelGales_${facturaId}.pdf`,
        image:        { type: 'jpeg', quality: 1.0 },
        html2canvas:  { 
            scale: 2, 
            useCORS: true, 
            letterRendering: true,
            scrollY: 0
        },
        jsPDF:        { unit: 'pt', format: 'letter', orientation: 'portrait' }
    };

    // Ocultar elementos que no queremos en el PDF
    const footer = document.querySelector('.invoice-footer');
    if (footer) footer.style.opacity = '0'; // Usamos opacity para no alterar el layout

    html2pdf().set(opt).from(element).save().then(() => {
        if (footer) footer.style.opacity = '1';
    });
}

// Guía fija de los colores del semáforo, a la izquierda de la página.
(function () {
  const COLORES = [
    ["verde", "Luz verde", "Pasa a veces. Se arregla hablando."],
    ["amarillo", "Luz amarilla", "Se repite o duele. Contale a un adulto de confianza."],
    ["rojo", "Luz roja", "Alguien lastima o amenaza. Buscá a un adulto ahora."],
  ];
  function poner() {
    if (document.getElementById("guia-semaforo")) return;
    const guia = document.createElement("aside");
    guia.id = "guia-semaforo";
    guia.setAttribute("aria-label", "Guía de colores del semáforo");
    guia.innerHTML =
      "<h2>🚦 Guía de colores</h2>" +
      COLORES.map(([c, t, d]) => `<div class="luz ${c}"><span class="punto"></span><div><b>${t}</b><p>${d}</p></div></div>`).join("") +
      "<p class=\"nota\">El color habla de lo que pasó, no de vos.</p>";
    document.body.appendChild(guia);
  }
  if (document.body) poner();
  document.addEventListener("DOMContentLoaded", poner);
})();

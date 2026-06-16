// ============================================================
// Utilitaires communs à toutes les pages de la borne arcade
// ============================================================

function afficherToast(message, type = "info") {
  const conteneur = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  conteneur.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.25s ease";
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

async function appelApi(url, options = {}) {
  try {
    const reponse = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return await reponse.json();
  } catch (erreur) {
    afficherToast("Erreur de connexion au serveur.", "error");
    return null;
  }
}

function demarrerHorloge() {
  const elementHorloge = document.getElementById("horloge");
  if (!elementHorloge) return;
  const maj = () => {
    const maintenant = new Date();
    elementHorloge.textContent = maintenant.toLocaleTimeString("fr-FR");
  };
  maj();
  setInterval(maj, 1000);
}

// ------------------------------------------------------------
// Modal générique mot de passe : renvoie une Promise<string|null>
// ------------------------------------------------------------
function demanderMotDePasse(titre, description) {
  return new Promise((resoudre) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal">
        <h3>${titre}</h3>
        <p>${description}</p>
        <div class="modal-error" id="modal-erreur">Mot de passe incorrect.</div>
        <input type="password" id="modal-mdp" placeholder="Mot de passe" autocomplete="off">
        <div class="modal-actions">
          <button class="btn btn-ghost" id="modal-annuler">Annuler</button>
          <button class="btn btn-primary" id="modal-valider">Valider</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("open"));

    const champ = overlay.querySelector("#modal-mdp");
    const erreurEl = overlay.querySelector("#modal-erreur");
    champ.focus();

    const fermer = (valeur) => {
      overlay.classList.remove("open");
      setTimeout(() => overlay.remove(), 180);
      resoudre(valeur);
    };

    overlay.querySelector("#modal-annuler").onclick = () => fermer(null);
    overlay.querySelector("#modal-valider").onclick = () => {
      if (!champ.value) {
        erreurEl.textContent = "Saisis un mot de passe.";
        erreurEl.classList.add("show");
        return;
      }
      fermer(champ.value);
    };
    champ.addEventListener("keydown", (e) => {
      erreurEl.classList.remove("show");
      if (e.key === "Enter") overlay.querySelector("#modal-valider").click();
      if (e.key === "Escape") fermer(null);
    });
  });
}

function demanderConfirmation(titre, description, labelValider = "Confirmer", danger = false) {
  return new Promise((resoudre) => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal">
        <h3>${titre}</h3>
        <p>${description}</p>
        <div class="modal-actions">
          <button class="btn btn-ghost" id="modal-annuler">Annuler</button>
          <button class="btn ${danger ? "btn-ghost btn-danger" : "btn-primary"}" id="modal-valider">${labelValider}</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add("open"));

    const fermer = (valeur) => {
      overlay.classList.remove("open");
      setTimeout(() => overlay.remove(), 180);
      resoudre(valeur);
    };
    overlay.querySelector("#modal-annuler").onclick = () => fermer(false);
    overlay.querySelector("#modal-valider").onclick = () => fermer(true);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  demarrerHorloge();
  initEcranVeille();
  initMusiqueAmbiance();
});

// ------------------------------------------------------------
// Écran de veille : apparaît après 90s d'inactivité, disparaît
// au moindre clic/touche/mouvement.
// ------------------------------------------------------------
const DELAI_VEILLE_MS = 90 * 1000;
let minuteurVeille = null;

function initEcranVeille() {
  const overlay = document.getElementById("ecran-veille");
  if (!overlay) return;

  const reinitialiserMinuteur = () => {
    clearTimeout(minuteurVeille);
    minuteurVeille = setTimeout(activerVeille, DELAI_VEILLE_MS);
  };

  const activerVeille = () => {
    overlay.classList.add("active");
    majStatsVeille();
    veilleHorlogeIntervalle = setInterval(majHorlogeVeille, 1000);
  };

  let veilleHorlogeIntervalle = null;

  const desactiverVeille = () => {
    if (overlay.classList.contains("active")) {
      overlay.classList.remove("active");
      clearInterval(veilleHorlogeIntervalle);
    }
    reinitialiserMinuteur();
  };

  ["click", "touchstart", "mousemove", "keydown"].forEach((evt) => {
    document.addEventListener(evt, desactiverVeille, { passive: true });
  });

  reinitialiserMinuteur();
}

function majHorlogeVeille() {
  const el = document.getElementById("veille-horloge");
  if (el) el.textContent = new Date().toLocaleTimeString("fr-FR");
}

async function majStatsVeille() {
  const el = document.getElementById("veille-stats");
  if (!el) return;
  const data = await appelApi("/api/systeme");
  if (data) {
    el.textContent = `${data.nb_jeux} jeux disponibles · ${data.nb_eleves || 0} élèves référencés`;
  }
}

// ------------------------------------------------------------
// Musique d'ambiance : lit en boucle les pistes déposées dans
// le dossier musique/ de la borne. Coupée par défaut (l'autoplay
// audio est bloqué par les navigateurs sans interaction).
// ------------------------------------------------------------
async function initMusiqueAmbiance() {
  const lecteur = document.getElementById("audio-ambiance");
  if (!lecteur) return;

  const pistes = await appelApi("/api/musique/liste");
  if (!pistes || pistes.length === 0) return;

  let indexPiste = 0;
  const chargerPiste = (i) => {
    lecteur.src = `/musique/${encodeURIComponent(pistes[i])}`;
  };
  chargerPiste(0);

  lecteur.addEventListener("ended", () => {
    indexPiste = (indexPiste + 1) % pistes.length;
    chargerPiste(indexPiste);
    lecteur.play().catch(() => {});
  });

  window.demarrerMusiqueAmbiance = () => {
    lecteur.volume = 0.35;
    lecteur.play().catch(() => {});
  };
  window.arreterMusiqueAmbiance = () => lecteur.pause();
  window.basculerMusiqueAmbiance = () => {
    if (lecteur.paused) window.demarrerMusiqueAmbiance();
    else window.arreterMusiqueAmbiance();
    return !lecteur.paused;
  };
}

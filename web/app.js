const { useEffect, useState } = React;

const VISTAS = [
  { id: "recetas", label: "Recetas" },
  { id: "semana", label: "Semana" },
  { id: "lista", label: "Lista" },
  { id: "despensa", label: "Despensa" },
];
const DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];
const COMIDAS = ["comida", "cena"];
const COMIDA_NOMBRE = { comida: "Comida", cena: "Cena" };
const PASILLO_NOMBRE = {
  verduras: "Verduras",
  fruteria: "Fruteria",
  carniceria: "Carniceria",
  pescaderia: "Pescaderia",
  lacteos: "Lacteos",
  panaderia: "Panaderia",
  despensa: "Despensa",
  congelados: "Congelados",
  bebidas: "Bebidas",
  otros: "Otros",
};

function ymd(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function lunesDeHoy() {
  const x = new Date();
  const local = new Date(x.getFullYear(), x.getMonth(), x.getDate());
  const dow = local.getDay();
  const delta = dow === 0 ? -6 : 1 - dow;
  local.setDate(local.getDate() + delta);
  return ymd(local);
}

function vistaDeHash() {
  const h = (location.hash || "#recetas").slice(1);
  if (["recetas", "semana", "lista", "despensa"].includes(h)) return h;
  return "recetas";
}

async function pedir(url, opciones) {
  let res;
  try {
    res = await fetch(url, opciones);
  } catch (err) {
    throw new Error("No conecta. Estan api y shopping con python app.py?");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || "Ha petado la peticion");
  }
  return data;
}

function moverLunes(semana, dias) {
  const partes = semana.split("-").map(Number);
  const x = new Date(partes[0], partes[1] - 1, partes[2]);
  x.setDate(x.getDate() + dias);
  return ymd(x);
}

function App() {
  const [vista, setVista] = useState(vistaDeHash);
  const [aviso, setAviso] = useState("");
  const [semana, setSemana] = useState(lunesDeHoy());

  useEffect(() => {
    const onHash = () => setVista(vistaDeHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  function ir(nombre) {
    location.hash = nombre;
    setVista(nombre);
  }

  return (
    <div>
      <header>
        <h1>RecipeBox</h1>
        <nav>
          {VISTAS.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-current={vista === item.id ? "page" : undefined}
              onClick={() => ir(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>
      <main>
        {aviso ? <p className="aviso" role="alert">{aviso}</p> : null}
        {vista === "semana" || vista === "lista" ? (
          <div className="panel fila">
            <button type="button" className="suave" onClick={() => setSemana(moverLunes(semana, -7))}>Semana anterior</button>
            <p>Lunes {semana}</p>
            <button type="button" className="suave" onClick={() => setSemana(moverLunes(semana, 7))}>Semana siguiente</button>
          </div>
        ) : null}
        {vista === "recetas" ? <Recetas alAviso={setAviso} /> : null}
        {vista === "semana" ? <Semana semana={semana} alAviso={setAviso} /> : null}
        {vista === "lista" ? <Lista semana={semana} alAviso={setAviso} /> : null}
        {vista === "despensa" ? <Despensa alAviso={setAviso} /> : null}
      </main>
    </div>
  );
}

function Recetas({ alAviso }) {
  const [recetas, setRecetas] = useState([]);
  const [abierta, setAbierta] = useState(null);
  const [listo, setListo] = useState(false);

  async function cargar() {
    try {
      setRecetas(await pedir(`${API_BASE}/recipes`));
    } catch (err) {
      alAviso(err.message);
    } finally {
      setListo(true);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function crear(ev) {
    ev.preventDefault();
    const data = new FormData(ev.target);
    try {
      await pedir(`${API_BASE}/recipes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: data.get("title"),
          servings: data.get("servings"),
          notes: data.get("notes"),
        }),
      });
      ev.target.reset();
      alAviso("");
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  async function borrar(id) {
    try {
      await pedir(`${API_BASE}/recipes/${id}`, { method: "DELETE" });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  return (
    <section>
      <div className="panel">
        <h2>Nueva receta</h2>
        <form onSubmit={crear}>
          <label>Titulo<input name="title" required /></label>
          <label>Raciones<input name="servings" type="number" min="1" defaultValue="2" /></label>
          <label>Notas<input name="notes" /></label>
          <button type="submit">Guardar</button>
        </form>
      </div>
      {listo && recetas.length === 0 ? <p>Aun no hay recetas. La de arriba es la primera.</p> : null}
      <ul className="lista">
        {recetas.map((r) => (
          <li key={r.id}>
            <span>{r.title} - {r.servings} raciones</span>
            <span>
              <button type="button" className="suave" onClick={() => setAbierta(r.id)}>Ingredientes</button>
              <button type="button" className="suave" onClick={() => borrar(r.id)}>Borrar</button>
            </span>
            {abierta === r.id ? <Detalle recetaId={r.id} alAviso={alAviso} /> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

function Detalle({ recetaId, alAviso }) {
  const [receta, setReceta] = useState(null);

  async function cargar() {
    try {
      setReceta(await pedir(`${API_BASE}/recipes/${recetaId}`));
    } catch (err) {
      alAviso(err.message);
    }
  }

  useEffect(() => { cargar(); }, [recetaId]);

  async function add(ev) {
    ev.preventDefault();
    const data = new FormData(ev.target);
    try {
      await pedir(`${API_BASE}/recipes/${recetaId}/ingredients`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"),
          quantity: data.get("quantity"),
          unit: data.get("unit"),
          aisle: data.get("aisle"),
        }),
      });
      ev.target.reset();
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  async function quitar(id) {
    try {
      await pedir(`${API_BASE}/ingredients/${id}`, { method: "DELETE" });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  if (!receta) return <p>Cargando...</p>;

  return (
    <div className="panel" style={{ width: "100%" }}>
      <ul className="lista">
        {(receta.ingredients || []).map((ing) => (
          <li key={ing.id}>
            <span>{ing.name} - {ing.quantity} {ing.unit} - {PASILLO_NOMBRE[ing.aisle] || ing.aisle}</span>
            <button type="button" className="suave" onClick={() => quitar(ing.id)}>Quitar</button>
          </li>
        ))}
      </ul>
      <form onSubmit={add}>
        <label>Ingrediente<input name="name" required /></label>
        <label>Cantidad<input name="quantity" type="number" step="0.1" defaultValue="1" /></label>
        <label>Unidad<input name="unit" placeholder="g, ud..." /></label>
        <label>Pasillo
          <select name="aisle" defaultValue="otros">
            {Object.keys(PASILLO_NOMBRE).map((p) => (
              <option key={p} value={p}>{PASILLO_NOMBRE[p]}</option>
            ))}
          </select>
        </label>
        <button type="submit">Anadir</button>
      </form>
    </div>
  );
}

function Semana({ semana, alAviso }) {
  const [plan, setPlan] = useState({ slots: [] });
  const [recetas, setRecetas] = useState([]);

  async function cargar() {
    try {
      const [p, r] = await Promise.all([
        pedir(`${API_BASE}/weeks/${semana}`),
        pedir(`${API_BASE}/recipes`),
      ]);
      setPlan(p);
      setRecetas(r);
    } catch (err) {
      alAviso(err.message);
    }
  }

  useEffect(() => { cargar(); }, [semana]);

  function slotDe(day, meal) {
    return (plan.slots || []).find((s) => s.day === day && s.meal === meal);
  }

  async function poner(day, meal, recipeId) {
    if (!recipeId) return;
    try {
      await pedir(`${API_BASE}/weeks/${semana}/slots`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          day,
          meal,
          recipe_id: Number(recipeId),
          servings: recetas.find((r) => r.id === Number(recipeId))?.servings || 2,
        }),
      });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  async function quitar(id) {
    try {
      await pedir(`${API_BASE}/slots/${id}`, { method: "DELETE" });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  async function raciones(id, servings) {
    try {
      await pedir(`${API_BASE}/slots/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ servings: Number(servings) }),
      });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  return (
    <section>
      <div className="semana">
        {DIAS.map((nombre, day) => (
          <article className="dia" key={nombre}>
            <h3>{nombre}</h3>
            {COMIDAS.map((meal) => {
              const slot = slotDe(day, meal);
              return (
                <div className="registro" key={meal}>
                  <strong>{COMIDA_NOMBRE[meal]}</strong>
                  {slot ? (
                    <p>
                      {slot.title}
                      <label>Raciones
                        <input
                          type="number"
                          min="1"
                          value={slot.servings}
                          onChange={(e) => raciones(slot.id, e.target.value)}
                        />
                      </label>
                      <button type="button" className="suave" onClick={() => quitar(slot.id)}>Quitar</button>
                    </p>
                  ) : (
                    <select defaultValue="" onChange={(e) => poner(day, meal, e.target.value)}>
                      <option value="">Elegir receta</option>
                      {recetas.map((r) => (
                        <option key={r.id} value={r.id}>{r.title}</option>
                      ))}
                    </select>
                  )}
                </div>
              );
            })}
          </article>
        ))}
      </div>
    </section>
  );
}

function Lista({ semana, alAviso }) {
  const [lista, setLista] = useState({ groups: [] });
  const [cargando, setCargando] = useState(true);
  const [diaCompra, setDiaCompra] = useState(5);
  const [horaCompra, setHoraCompra] = useState("11:00");

  async function cargar() {
    setCargando(true);
    try {
      setLista(await pedir(`${SHOP_BASE}/list?week=${semana}`));
    } catch (err) {
      alAviso(err.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { cargar(); }, [semana]);

  return (
    <section className="panel">
      <p>
        <a href={`${SHOP_BASE}/pdf?week=${semana}`}>Descargar PDF</a>
      </p>
      <p>
        <label>Dia de la compra
          <select value={diaCompra} onChange={(e) => setDiaCompra(Number(e.target.value))}>
            {DIAS.map((nombre, i) => (
              <option key={nombre} value={i}>{nombre}</option>
            ))}
          </select>
        </label>
      </p>
      <p>
        <label>Hora
          <input type="time" value={horaCompra} onChange={(e) => setHoraCompra(e.target.value)} />
        </label>
      </p>
      <p>
        <a href={`${SHOP_BASE}/ics?week=${semana}&shop_day=${diaCompra}&shop_hour=${horaCompra}`}>
          Anadir al calendario
        </a>
      </p>
      {cargando ? <p>Cargando lista...</p> : null}
      {!cargando && (lista.groups || []).length === 0 ? <p>No hay nada que comprar.</p> : null}
      {(lista.groups || []).map((g) => (
        <div key={g.aisle}>
          <h3>{PASILLO_NOMBRE[g.aisle] || g.aisle}</h3>
          <ul>
            {g.items.map((item) => (
              <li key={item.name + item.unit}>
                {item.name} - {item.quantity} {item.unit}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function Despensa({ alAviso }) {
  const [items, setItems] = useState([]);

  async function cargar() {
    try {
      setItems(await pedir(`${SHOP_BASE}/pantry`));
    } catch (err) {
      alAviso(err.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  async function crear(ev) {
    ev.preventDefault();
    const data = new FormData(ev.target);
    try {
      await pedir(`${SHOP_BASE}/pantry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.get("name"),
          quantity: data.get("quantity"),
          unit: data.get("unit"),
        }),
      });
      ev.target.reset();
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  async function quitar(id) {
    try {
      await pedir(`${SHOP_BASE}/pantry/${id}`, { method: "DELETE" });
      cargar();
    } catch (err) {
      alAviso(err.message);
    }
  }

  return (
    <section>
      <div className="panel">
        <h2>Lo que ya tengo</h2>
        <form onSubmit={crear}>
          <label>Producto<input name="name" required /></label>
          <label>Cantidad<input name="quantity" type="number" step="0.1" defaultValue="1" /></label>
          <label>Unidad<input name="unit" /></label>
          <button type="submit">Guardar</button>
        </form>
      </div>
      <ul className="lista">
        {items.map((item) => (
          <li key={item.id}>
            <span>{item.name} - {item.quantity} {item.unit}</span>
            <button type="button" className="suave" onClick={() => quitar(item.id)}>Quitar</button>
          </li>
        ))}
      </ul>
    </section>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

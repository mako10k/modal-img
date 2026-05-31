function App() {
  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">modal-img</p>
        <h1>Quality-first image generation</h1>
        <p className="lead">
          FastAPI と Modal を土台に、品質優先で画像生成基盤を構築する。
        </p>
        <ul className="stack">
          <li>Backend: Python 3.12 / FastAPI / Modal</li>
          <li>Queue and DB: Redis / PostgreSQL</li>
          <li>Frontend: React / TypeScript / Vite</li>
        </ul>
      </section>
    </main>
  );
}

export default App;

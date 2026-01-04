
import React, { useState, useEffect } from 'react';
import {
  Year,
  Event,
  Session,
  Driver,
  ExportType,
  LapSelector,
  OptionsState,
  SelectionState
} from './types';

// Components
const Header: React.FC = () => (
  <header className="border-b border-neutral-800 pt-8 pb-6 px-4 mb-12">
    <div className="max-w-3xl mx-auto flex flex-col md:flex-row justify-between items-baseline gap-4">
      <div>
        <h1 className="text-4xl md:text-5xl font-black italic tracking-tighter uppercase leading-none">
          Se Viene Un <span className="text-[#FF1801]">Safety</span>
        </h1>
        <p className="text-neutral-500 font-mono text-xs mt-2 tracking-widest uppercase">
          Herramienta apta para boludos
        </p>
      </div>
      <div className="text-right hidden md:block">
        <span className="text-neutral-700 font-mono text-xs uppercase">Race-Control v3.14.0</span>
      </div>
    </div>
  </header>
);

const SectionTitle: React.FC<{ title: string; number: string }> = ({ title, number }) => (
  <div className="flex items-center gap-3 mb-6 border-l-2 border-[#FF1801] pl-4">
    <span className="font-mono text-neutral-600 text-sm">{number}</span>
    <h2 className="text-xl font-bold uppercase tracking-tight">{title}</h2>
  </div>
);

// Export Configuration Metadata
const EXPORT_CONFIG: Record<ExportType, {
  displayName: string;
  description: string;
  driverSelection: 'OPTIONAL' | 'REQUIRED' | 'DISABLED' | 'COMPARE_TWO' | 'TEAM_PAIRS';
  scopeSelection: 'ENABLED' | 'DISABLED';
}> = {
  [ExportType.LAPS]: {
    displayName: "Resumen de Vueltas",
    description: "Tiempos de vuelta y sectores básicos para conductores seleccionados (por defecto: todos).",
    driverSelection: 'OPTIONAL',
    scopeSelection: 'ENABLED'
  },
  [ExportType.TELEMETRY]: {
    displayName: "Telemetría Bruta",
    description: "Datos de alta frecuencia de velocidad, acelerador y freno. Advertencia: Archivos grandes.",
    driverSelection: 'OPTIONAL',
    scopeSelection: 'ENABLED'
  },
  [ExportType.COMPARE]: {
    displayName: "Análisis Comparativo",
    description: "Comparación de telemetría lado a lado de exactamente dos conductores en sus vueltas más rápidas.",
    driverSelection: 'COMPARE_TWO',
    scopeSelection: 'DISABLED'
  },
  [ExportType.TEAM_PARTNERS]: {
    displayName: "Análisis Compañeros de Equipo",
    description: "Compara compañeros de equipo en todos los equipos. Incluye automáticamente todos los pares.",
    driverSelection: 'DISABLED',
    scopeSelection: 'DISABLED'
  },
  [ExportType.FINAL_SPEED]: {
    displayName: "Velocidades Finales (Max V)",
    description: "Velocidad máxima alcanzada por cada conductor en su vuelta más rápida (proxy de final de recta).",
    driverSelection: 'DISABLED',
    scopeSelection: 'DISABLED'
  },
  [ExportType.RACE_PACE]: {
    displayName: "Ranking de Ritmo de Carrera",
    description: "Clasifica a todos los conductores por ritmo de carrera mediano, excluyendo paradas en boxes y Safety Cars.",
    driverSelection: 'DISABLED',
    scopeSelection: 'DISABLED'
  },
  [ExportType.POLE_MICROSECTORS]: {
    displayName: "Telemetría Pole Año Anterior",
    description: "Telemetría por microsectores de la vuelta de pole position del año anterior.",
    driverSelection: 'DISABLED',
    scopeSelection: 'DISABLED'
  }
};

const App: React.FC = () => {
  const [options, setOptions] = useState<OptionsState>({
    years: [],
    events: [],
    sessions: [],
    drivers: []
  });

  const [selection, setSelection] = useState<SelectionState>({
    year: '',
    event: '',
    session: '',
    selectedDrivers: [],
    type: ExportType.LAPS,
    lap: LapSelector.FASTEST,
    lapNumber: '1'
  });

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // New State for Notification
  const [latestEvent, setLatestEvent] = useState<{ year: number, event: string, session: string } | null>(null);

  // Helper fetchers
  const fetchEvents = async (year: string) => {
    const res = await fetch(`/options/events?year=${year}`);
    if (!res.ok) throw new Error('Failed to fetch events');
    return res.json();
  };

  const fetchSessions = async (year: string, event: string) => {
    const res = await fetch(`/options/sessions?year=${year}&event=${event}`);
    if (!res.ok) throw new Error('Failed to fetch sessions');
    return res.json();
  };

  const fetchDrivers = async (year: string, event: string, session: string) => {
    const res = await fetch(`/options/drivers?year=${year}&event=${event}&session=${session}`);
    if (!res.ok) throw new Error('Failed to fetch drivers');
    const data = await res.json();
    return data.map((d: any) => d.code).filter(Boolean);
  };

  // Initial load
  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true);
        // Load years
        const res = await fetch('/options/years');
        if (!res.ok) throw new Error('Failed to fetch years');
        const data = await res.json();
        setOptions(prev => ({ ...prev, years: data.sort((a: number, b: number) => b - a) }));

        // Check for latest event
        const latestRes = await fetch('/latest/event');
        if (latestRes.ok) {
          const latestData = await latestRes.json();
          if (latestData.found) {
            setLatestEvent(latestData);
          }
        }
      } catch (err) {
        setError("Failed to initialize app.");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  // Handlers with integrated fetching
  const handleYearChange = async (newYear: string) => {
    setSelection(prev => ({ ...prev, year: newYear, event: '', session: '', selectedDrivers: [] }));
    if (!newYear) return;

    try {
      setLoading(true);
      const events = await fetchEvents(newYear);
      setOptions(prev => ({ ...prev, events, sessions: [], drivers: [] }));
    } catch (e) {
      setError("Failed to load events.");
    } finally {
      setLoading(false);
    }
  };

  const handleEventChange = async (newEvent: string) => {
    setSelection(prev => ({ ...prev, event: newEvent, session: '', selectedDrivers: [] }));
    if (!selection.year || !newEvent) return;

    try {
      setLoading(true);
      const sessions = await fetchSessions(selection.year, newEvent);
      setOptions(prev => ({ ...prev, sessions, drivers: [] }));
    } catch (e) {
      setError("Failed to load sessions.");
    } finally {
      setLoading(false);
    }
  };

  const handleSessionChange = async (newSession: string) => {
    setSelection(prev => ({ ...prev, session: newSession, selectedDrivers: [] }));
    if (!selection.year || !selection.event || !newSession) return;

    try {
      setLoading(true);
      const drivers = await fetchDrivers(selection.year, selection.event, newSession);
      setOptions(prev => ({ ...prev, drivers }));
    } catch (e) {
      setError("Failed to load drivers.");
    } finally {
      setLoading(false);
    }
  };

  const loadLatest = async () => {
    if (!latestEvent) return;
    try {
      setLoading(true);
      setLatestEvent(null); // Dismiss notification logic

      const { year, event, session } = latestEvent;
      const yearStr = year.toString();

      // Fetch all necessary data
      // 1. Events
      const events = await fetchEvents(yearStr);
      // 2. Sessions
      const sessions = await fetchSessions(yearStr, event);
      // 3. Drivers
      const drivers = await fetchDrivers(yearStr, event, session);

      setOptions(prev => ({ ...prev, events, sessions, drivers }));
      setSelection(prev => ({
        ...prev,
        year: yearStr,
        event: event,
        session: session,
        selectedDrivers: []
      }));

    } catch (e) {
      console.error(e);
      setError("Failed to auto-load latest event.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!selection.year || !selection.event || !selection.session) {
      setError("Complete required fields.");
      return;
    }

    const config = EXPORT_CONFIG[selection.type];

    // Validation Rules
    if (config.driverSelection === 'COMPARE_TWO' && selection.selectedDrivers.length !== 2) {
      setError("This export requires exactly 2 drivers selected.");
      return;
    }

    const driversToSend = config.driverSelection === 'DISABLED' ? [] : selection.selectedDrivers;

    setError(null);
    const query = new URLSearchParams({
      year: selection.year,
      event: selection.event,
      session: selection.session,
      drivers: driversToSend.join(','),
      type: selection.type,
      lap: selection.lap,
      lap_number: selection.lapNumber
    });
    window.open(`/export.csv?${query.toString()}`, '_blank');
  };

  const toggleDriver = (driver: Driver) => {
    const config = EXPORT_CONFIG[selection.type];
    if (config.driverSelection === 'DISABLED') return;

    setSelection(prev => {
      const isSelected = prev.selectedDrivers.includes(driver);

      if (!isSelected && config.driverSelection === 'COMPARE_TWO' && prev.selectedDrivers.length >= 2) {
        return prev;
      }

      if (isSelected) {
        return { ...prev, selectedDrivers: prev.selectedDrivers.filter(d => d !== driver) };
      } else {
        return { ...prev, selectedDrivers: [...prev.selectedDrivers, driver] };
      }
    });
  };

  const currentConfig = EXPORT_CONFIG[selection.type];

  return (
    <div className="min-h-screen pb-20 relative">
      <Header />

      {/* Latest Event Notification */}
      {latestEvent && (
        <div className="max-w-3xl mx-auto px-4 mb-8">
          <div className="bg-neutral-900 border border-[#FF1801] p-4 flex flex-col sm:flex-row justify-between items-center gap-4 shadow-[0_0_20px_rgba(255,24,1,0.15)]">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-[#FF1801] rounded-full animate-pulse"></div>
              <div>
                <div className="text-[#FF1801] font-mono text-[10px] uppercase tracking-widest leading-none mb-1">Nuevo Evento Detectado</div>
                <div className="text-white font-bold uppercase tracking-tight">{latestEvent.event} ({latestEvent.year})</div>
              </div>
            </div>
            <button
              onClick={loadLatest}
              className="bg-[#FF1801] hover:bg-white hover:text-[#FF1801] text-white px-6 py-2 font-black uppercase text-sm tracking-tighter transition-colors"
            >
              Cargar Datos
            </button>
          </div>
        </div>
      )}

      <main className="max-w-3xl mx-auto px-4">
        {error && (
          <div className="bg-[#FF1801] text-white px-4 py-2 mb-8 font-mono text-sm uppercase flex justify-between items-center">
            <span>ERROR: {error}</span>
            <button onClick={() => setError(null)} className="hover:opacity-70">✕</button>
          </div>
        )}

        {/* 1. SESSION SELECTION */}
        <section className="mb-12">
          <SectionTitle title="Búsqueda de Sesión" number="01" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-neutral-800 border border-neutral-800">
            <div className="bg-[#0B0B0B] p-4">
              <label className="block text-neutral-500 font-mono text-[10px] uppercase mb-1">Año</label>
              <select
                value={selection.year}
                onChange={(e) => handleYearChange(e.target.value)}
                className="w-full bg-[#0B0B0B] text-white border-none outline-none appearance-none font-bold text-lg cursor-pointer"
              >
                <option value="" disabled>SELECCIONAR AÑO</option>
                {options.years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div className={`bg-[#0B0B0B] p-4 ${!selection.year && 'opacity-30 pointer-events-none'}`}>
              <label className="block text-neutral-500 font-mono text-[10px] uppercase mb-1">Evento</label>
              <select
                value={selection.event}
                onChange={(e) => handleEventChange(e.target.value)}
                className="w-full bg-[#0B0B0B] text-white border-none outline-none appearance-none font-bold text-lg cursor-pointer truncate"
              >
                <option value="" disabled>SELECCIONAR EVENTO</option>
                {options.events.map(e => <option key={e} value={e}>{e.toUpperCase()}</option>)}
              </select>
            </div>
            <div className={`bg-[#0B0B0B] p-4 ${(!selection.year || !selection.event) && 'opacity-30 pointer-events-none'}`}>
              <label className="block text-neutral-500 font-mono text-[10px] uppercase mb-1">Sesión</label>
              <select
                value={selection.session}
                onChange={(e) => handleSessionChange(e.target.value)}
                className="w-full bg-[#0B0B0B] text-white border-none outline-none appearance-none font-bold text-lg cursor-pointer"
              >
                <option value="" disabled>ID SESIÓN</option>
                {options.sessions.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </section>

        {/* 2. DRIVER SELECTION */}
        <section className={`mb-12 transition-opacity ${(!selection.session) && 'opacity-30 pointer-events-none'}`}>
          <SectionTitle title="Configuración de Pilotos" number="02" />
          <div className="border border-neutral-800 p-6">
            <div className="flex justify-between items-center mb-4">
              <label className="block text-neutral-500 font-mono text-[10px] uppercase tracking-widest">Conductores Seleccionados</label>
              {/* Visual indicator of mode */}
              <span className="text-neutral-600 font-mono text-[10px] uppercase">
                Modo: <span className="text-[#FF1801]">{currentConfig.driverSelection}</span>
              </span>
            </div>

            {currentConfig.driverSelection === 'DISABLED' ? (
              <div className="p-4 bg-neutral-900 border border-neutral-800 text-neutral-400 font-mono text-xs italic text-center">
                Esta exportación incluye automáticamente a todo el campo o objetivos específicos. <br />
                La selección manual de conductores está deshabilitada.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {options.drivers.map(driver => (
                  <button
                    key={driver}
                    onClick={() => toggleDriver(driver)}
                    disabled={currentConfig.driverSelection === 'DISABLED'}
                    className={`px-4 py-2 font-mono text-sm border transition-colors ${selection.selectedDrivers.includes(driver)
                      ? 'bg-white text-black border-white font-bold'
                      : 'bg-transparent text-neutral-400 border-neutral-800 hover:border-neutral-500'
                      } ${currentConfig.driverSelection === 'DISABLED' ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {driver}
                  </button>
                ))}
                {options.drivers.length === 0 && (
                  <span className="text-neutral-700 italic font-mono text-xs">Esperando definición de sesión...</span>
                )}
              </div>
            )}
          </div>
        </section>

        {/* 3. EXPORT SETTINGS */}
        <section className={`mb-12 transition-opacity ${!selection.session && 'opacity-30 pointer-events-none'}`}>
          <SectionTitle title="Parámetros de Exportación" number="03" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 p-6 border border-neutral-800">
            <div>
              <label className="block text-neutral-500 font-mono text-[10px] uppercase mb-2 tracking-widest">Formato de Salida</label>
              <select
                value={selection.type}
                onChange={(e) => setSelection(prev => ({ ...prev, type: e.target.value as ExportType }))}
                className="w-full bg-neutral-900 text-white border border-neutral-700 p-3 font-bold uppercase tracking-tighter outline-none focus:border-[#FF1801]"
              >
                {Object.values(ExportType).map((type) => (
                  <option key={type} value={type}>
                    {EXPORT_CONFIG[type].displayName}
                  </option>
                ))}
              </select>
              {/* Description Box */}
              <div className="mt-4 p-3 border border-neutral-800 bg-neutral-900/50">
                <p className="text-neutral-400 font-mono text-xs leading-relaxed">
                  <span className="text-white font-bold mr-2">[INFO]</span>
                  {currentConfig.description}
                </p>
              </div>
            </div>
            <div className={`transition-opacity ${currentConfig.scopeSelection === 'DISABLED' ? 'opacity-30 pointer-events-none' : ''}`}>
              <label className="block text-neutral-500 font-mono text-[10px] uppercase mb-2 tracking-widest">Alcance</label>
              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => setSelection(prev => ({ ...prev, lap: LapSelector.FASTEST }))}
                  className={`flex-1 p-3 text-xs font-mono uppercase border ${selection.lap === LapSelector.FASTEST ? 'bg-white text-black border-white' : 'border-neutral-700 text-neutral-500'}`}
                >
                  Más Rápida
                </button>
                <button
                  onClick={() => setSelection(prev => ({ ...prev, lap: LapSelector.LAP_NUMBER }))}
                  className={`flex-1 p-3 text-xs font-mono uppercase border ${selection.lap === LapSelector.LAP_NUMBER ? 'bg-white text-black border-white' : 'border-neutral-700 text-neutral-500'}`}
                >
                  Por Vuelta #
                </button>
              </div>
              {selection.lap === LapSelector.LAP_NUMBER && (
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={selection.lapNumber}
                  onChange={(e) => setSelection(prev => ({ ...prev, lapNumber: e.target.value }))}
                  className="w-full bg-neutral-900 text-white border border-neutral-700 p-2 font-mono text-center outline-none focus:border-[#FF1801]"
                  placeholder="Nº VUELTA"
                />
              )}
            </div>
          </div>
        </section>

        {/* 4. EXECUTION */}
        <div className="mt-16 flex flex-col items-center">
          {loading && (
            <div className="mb-4 flex items-center gap-4">
              <div className="h-1 w-24 bg-neutral-800 overflow-hidden relative">
                <div className="absolute top-0 left-0 h-full w-1/3 bg-[#FF1801] animate-[loading_1s_infinite_linear]"></div>
              </div>
              <span className="font-mono text-[10px] uppercase text-neutral-600 tracking-tighter">Sincronizando con Race Control...</span>
            </div>
          )}

          <button
            disabled={!selection.session || loading}
            onClick={handleDownload}
            className={`
              w-full py-6 text-2xl font-black uppercase tracking-tighter border-2
              transition-all duration-300 transform active:scale-[0.98]
              ${!selection.session || loading
                ? 'border-neutral-800 text-neutral-800 cursor-not-allowed'
                : 'border-[#FF1801] bg-[#FF1801] text-white hover:bg-white hover:text-[#FF1801] shadow-[0_0_30px_rgba(255,24,1,0.2)]'
              }
            `}
          >
            {loading ? 'Procesando...' : 'Exportar CSV'}
          </button>

          <div className="mt-8 text-neutral-700 font-mono text-[9px] uppercase tracking-widest text-center leading-relaxed">
            FastF1 es un proyecto independiente. <br />
            La fidelidad de los datos depende de la integridad de la sesión. <br />
            <span className="text-[#FF1801]">¿Sin datos? Problema de habilidad.</span>
          </div>
        </div>
      </main>

      <style>{`
        @keyframes loading {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>
    </div>
  );
};

export default App;

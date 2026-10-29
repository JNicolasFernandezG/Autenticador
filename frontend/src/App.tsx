import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Users,
  Search,
  Plus,
  KeyRound,
  CheckCircle2,
  XCircle,
  Link2,
  LogOut,
  Server,
  RefreshCw,
  Terminal,
  Copy,
  Check,
  ExternalLink,
  Settings2,
  Gamepad2,
  Trash2,
} from 'lucide-react';
import {
  api,
  Usuario,
  ServicioCatalogo,
  EstadoUsuario,
  MagicLinkServicioItem,
} from './api';

export default function App() {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('auth_admin_token')
  );

  // SSO State
  const [jumpingToGames, setJumpingToGames] = useState(false);

  // Detección automática de Ticket SSO al ingresar al panel
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ticketParam = params.get('ticket');
    if (ticketParam) {
      window.history.replaceState({}, document.title, window.location.pathname);
      setLoading(true);
      api.consumirTicketSSO(ticketParam, 'autenticador')
        .then((res) => {
          localStorage.setItem('auth_admin_token', res.token);
          localStorage.setItem('auth_admin_user', JSON.stringify(res.user));
          setToken(res.token);
          setAdminUser(res.user);
          notify(`Bienvenido vía SSO: ${res.user.name}`);
        })
        .catch((err: any) => {
          console.error('Error al canjear ticket SSO:', err);
          notify(err.message || 'Ticket SSO inválido o expirado', 'err');
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, []);

  const handleIrAJuegosAdmin = async () => {
    if (!token || jumpingToGames) return;
    setJumpingToGames(true);
    try {
      const res = await api.generarTicketSSO(token, 'cognijuegos');
      if (res && res.ticket) {
        const juegosAdminUrl = (import.meta as any).env?.VITE_JUEGOS_ADMIN_URL || 'https://cognijuegos.asistodo.com.ar/admin';
        window.location.href = `${juegosAdminUrl}?ticket=${encodeURIComponent(res.ticket)}`;
      }
    } catch (err: any) {
      console.error('Error al generar ticket SSO hacia Juegos:', err);
      notify(err.message || 'Error al iniciar salto SSO hacia Juegos', 'err');
      setJumpingToGames(false);
    }
  };
  const [adminUser, setAdminUser] = useState<Usuario | null>(() => {
    const raw = localStorage.getItem('auth_admin_user');
    return raw ? JSON.parse(raw) : null;
  });

  // Login states
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loggingIn, setLoggingIn] = useState(false);

  // Dashboard states
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [loading, setLoading] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [filterServicio, setFilterServicio] = useState('');
  const [filterActivo, setFilterActivo] = useState<string>('');

  // Catalogs
  const [serviciosCatalogo, setServiciosCatalogo] = useState<ServicioCatalogo[]>([]);
  const [estadosCatalogo, setEstadosCatalogo] = useState<EstadoUsuario[]>([]);

  // Notifications / Toasts
  const [toast, setToast] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  // Modals
  const [showNewUserModal, setShowNewUserModal] = useState(false);
  const [showNewServiceModal, setShowNewServiceModal] = useState(false);
  const [editingService, setEditingService] = useState<ServicioCatalogo | null>(null);
  const [magicLinkData, setMagicLinkData] = useState<{
    userName: string;
    codigoAcceso: string;
    token: string;
    magicLinksList: MagicLinkServicioItem[];
  } | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // New user form
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPin, setNewPin] = useState('');
  const [newTipo, setNewTipo] = useState(1);
  const [newServicios, setNewServicios] = useState<Record<string, boolean>>({
    mayoresactualizaciones: true,
    cognijuegos: true,
  });

  // New service form
  const [srvClave, setSrvClave] = useState('');
  const [srvNombre, setSrvNombre] = useState('');
  const [srvUrlBase, setSrvUrlBase] = useState('https://mayoresactualizaciones.asistodo.com.ar');
  const [srvRutaMagic, setSrvRutaMagic] = useState('/acceso');
  const [srvDesc, setSrvDesc] = useState('');

  // Simulator form
  const [simIdentifier, setSimIdentifier] = useState('marta.gonzalez@ejemplo.com');
  const [simServicio, setSimServicio] = useState('mayoresactualizaciones');
  const [simResult, setSimResult] = useState<any>(null);
  const [simLoading, setSimLoading] = useState(false);

  const notify = (text: string, type: 'ok' | 'err' = 'ok') => {
    setToast({ text, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setLoggingIn(true);
    try {
      const res = await api.loginAdmin(loginEmail, loginPassword);
      if (res.user.tipoUsuario !== 2) {
        throw new Error('Esta consola es exclusiva para Administradores (tipoUsuario = 2).');
      }
      localStorage.setItem('auth_admin_token', res.token);
      localStorage.setItem('auth_admin_user', JSON.stringify(res.user));
      setToken(res.token);
      setAdminUser(res.user);
    } catch (err: any) {
      setLoginError(err.message || 'Error al iniciar sesión');
    } finally {
      setLoggingIn(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_admin_token');
    localStorage.removeItem('auth_admin_user');
    setToken(null);
    setAdminUser(null);
  };

  const fetchCatalogs = async () => {
    if (!token) return;
    try {
      const [srvRes, estRes] = await Promise.all([
        api.getServiciosCatalogo(token),
        api.getEstadosCatalogo(token),
      ]);
      setServiciosCatalogo(srvRes.servicios);
      setEstadosCatalogo(estRes.estados);
    } catch (err: any) {
      if (String(err.message).includes('401') || String(err.message).includes('expirado')) {
        handleLogout();
      }
    }
  };

  const fetchUsuarios = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await api.getUsuarios(token, {
        limit,
        skip,
        nombre: search || undefined,
        servicio: filterServicio || undefined,
        activo: filterActivo === '' ? undefined : filterActivo === 'true',
        orden: 'desc',
      });
      setUsuarios(res.items);
      setTotal(res.total);
    } catch (err: any) {
      notify(err.message || 'Error cargando usuarios', 'err');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCatalogs();
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchUsuarios();
    }
  }, [token, skip, search, filterServicio, filterActivo]);

  const handleToggleServicio = async (userId: number, clave: string) => {
    if (!token) return;
    try {
      const res = await api.toggleServicio(token, userId, clave);
      setUsuarios((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, servicios: res.servicios } : u))
      );
      notify(res.message, 'ok');
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleToggleActivo = async (userId: number) => {
    if (!token) return;
    try {
      const res = await api.toggleActivo(token, userId);
      setUsuarios((prev) =>
        prev.map((u) =>
          u.id === userId
            ? {
                ...u,
                activo: res.activo,
                estadoId: res.activo ? 2 : 3,
                estadoCodigo: res.activo ? 'ACTIVO' : 'SUSPENDIDO',
              }
            : u
        )
      );
      notify(res.message, 'ok');
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleEliminarUsuario = async (u: Usuario) => {
    if (!token) return;
    if (u.tipoUsuario === 2 || u.email.toLowerCase() === 'admin@autenticador.com') {
      notify('La cuenta de Administrador Central está protegida y no puede ser eliminada.', 'err');
      return;
    }
    const ok = window.confirm(
      `¿Estás seguro de que deseas eliminar permanentemente al usuario #${u.id} (${u.name} - ${u.email})?\nEsta acción no se puede deshacer.`
    );
    if (!ok) return;

    try {
      const res = await api.eliminarUsuario(token, u.id);
      setUsuarios((prev) => prev.filter((item) => item.id !== u.id));
      setTotal((prev) => Math.max(0, prev - 1));
      notify(res.message, 'ok');
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleCambiarEstado = async (userId: number, estadoId: number) => {
    if (!token) return;
    try {
      const res = await api.cambiarEstado(token, userId, estadoId);
      setUsuarios((prev) =>
        prev.map((u) =>
          u.id === userId
            ? {
                ...u,
                estadoId: res.estado_id,
                estadoCodigo: res.estado_codigo,
                activo: res.activo,
              }
            : u
        )
      );
      notify(res.message, 'ok');
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleMagicLink = async (u: Usuario) => {
    if (!token) return;
    try {
      const res = await api.generarMagicLink(token, u.id);
      setMagicLinkData({
        userName: u.name,
        codigoAcceso: res.codigoAcceso,
        token: res.token,
        magicLinksList: res.magicLinksList || [],
      });
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const created = await api.crearUsuario(token, {
        name: newName,
        email: newEmail,
        codigoAcceso: newPin || undefined,
        tipoUsuario: newTipo,
        activo: true,
        servicios: newServicios,
      });
      notify(`Usuario '${newName}' creado exitosamente.`);
      setShowNewUserModal(false);
      setNewName('');
      setNewEmail('');
      setNewPin('');
      await fetchUsuarios();
      // Abrir inmediatamente los Magic Links de cada servicio para el nuevo usuario
      handleMagicLink(created);
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleCreateService = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const res = await api.crearServicioCatalogo(token, {
        clave: srvClave,
        nombre: srvNombre,
        url_base: srvUrlBase,
        ruta_magic_link: srvRutaMagic,
        descripcion: srvDesc,
      });
      notify(res.message);
      setShowNewServiceModal(false);
      setSrvClave('');
      setSrvNombre('');
      setSrvUrlBase('https://mayoresactualizaciones.asistodo.com.ar');
      setSrvRutaMagic('/acceso');
      setSrvDesc('');
      fetchCatalogs();
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleUpdateServiceUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !editingService) return;
    try {
      const res = await api.actualizarServicioCatalogo(token, editingService.clave, {
        nombre: editingService.nombre,
        url_base: editingService.url_base,
        ruta_magic_link: editingService.ruta_magic_link,
        descripcion: editingService.descripcion,
      });
      notify(res.message);
      setEditingService(null);
      fetchCatalogs();
    } catch (err: any) {
      notify(err.message, 'err');
    }
  };

  const handleSimularValidacion = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimLoading(true);
    try {
      const isPin = /^\d{4,8}$/.test(simIdentifier.trim());
      const res = await api.simularValidacionServicio({
        email: isPin ? undefined : simIdentifier.trim(),
        codigoAcceso: isPin ? simIdentifier.trim() : undefined,
        servicio: simServicio,
      });
      setSimResult(res);
    } catch (err: any) {
      setSimResult({ success: false, allowed: false, message: err.message });
    } finally {
      setSimLoading(false);
    }
  };

  const copyText = (key: string, value: string) => {
    navigator.clipboard.writeText(value);
    setCopiedField(key);
    notify('Copiado al portapapeles');
    setTimeout(() => setCopiedField(null), 2000);
  };

  // ---------------- VISTA DE LOGIN EXCLUSIVA PARA ADMIN ----------------
  if (!token) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Autenticador Central</h1>
              <p className="text-xs text-slate-400">
                Torre de Control — Acceso exclusivo Administrador
              </p>
            </div>
          </div>

          {loginError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Email Administrador
              </label>
              <input
                type="email"
                required
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
                placeholder="correo@ejemplo.com"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Contraseña o PIN Maestro
              </label>
              <input
                type="password"
                required
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loggingIn}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition flex items-center justify-center gap-2"
            >
              <KeyRound className="w-4 h-4" />
              {loggingIn ? 'Verificando credenciales...' : 'Ingresar a la Torre de Control'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  const clavesServicios: ServicioCatalogo[] =
    serviciosCatalogo.length > 0
      ? serviciosCatalogo
      : [
          {
            clave: 'mayoresactualizaciones',
            nombre: 'Mayores Actualizaciones',
            descripcion: 'Plataforma SIPI',
            url_base: 'https://mayoresactualizaciones.asistodo.com.ar',
            ruta_magic_link: '/acceso',
            color: 'indigo',
            activo: true,
          },
          {
            clave: 'cognijuegos',
            nombre: 'CogniJuegos',
            descripcion: 'Entrenamiento Cognitivo',
            url_base: 'https://cognijuegos.asistodo.com.ar',
            ruta_magic_link: '/acceso',
            color: 'teal',
            activo: true,
          },
        ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed bottom-5 right-5 z-50 px-4 py-3 rounded-xl border shadow-xl text-sm font-medium flex items-center gap-2 ${
            toast.type === 'ok'
              ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
              : 'bg-rose-950/90 border-rose-500/40 text-rose-200'
          }`}
        >
          {toast.type === 'ok' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          ) : (
            <XCircle className="w-4 h-4 text-rose-400" />
          )}
          {toast.text}
        </div>
      )}

      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white">
                  Autenticador Central — Torre de Control
                </h1>
                <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  MongoDB Conectado
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Gestión de cuentas y Magic Links independientes por servicio (
                <code className="text-indigo-300">mayoresactualizaciones</code>,{' '}
                <code className="text-teal-300">cognijuegos</code>, etc.)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleIrAJuegosAdmin}
              disabled={jumpingToGames}
              className="px-3 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 text-xs font-semibold flex items-center gap-1.5 border border-emerald-500/30 transition disabled:opacity-50 cursor-pointer"
              title="Acceder a la Torre de Control de Juegos sin ingresar credenciales (SSO)"
            >
              <Gamepad2 className="w-3.5 h-3.5 text-emerald-400" />
              {jumpingToGames ? 'Conectando...' : 'Torre de Juegos (SSO)'}
            </button>
            <button
              onClick={() => setShowNewServiceModal(true)}
              className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 border border-slate-700 transition"
            >
              <Server className="w-3.5 h-3.5 text-teal-400" />
              + Registrar Clave de Servicio
            </button>
            <button
              onClick={() => setShowNewUserModal(true)}
              className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
            >
              <Plus className="w-4 h-4" />
              Nuevo Usuario
            </button>
            <div className="h-5 w-px bg-slate-800 mx-1" />
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-white">{adminUser?.name}</p>
              <p className="text-[11px] text-slate-400">{adminUser?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Cerrar sesión"
              className="p-2 rounded-lg bg-slate-800 hover:bg-rose-500/20 hover:text-rose-300 text-slate-400 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {/* Tarjetas de Servicios y Configuración de URL de Magic Link */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>Total Cuentas Registradas</span>
                <Users className="w-4 h-4 text-indigo-400" />
              </div>
              <p className="text-2xl font-bold text-white">{total}</p>
            </div>
            <p className="text-[11px] text-slate-400 mt-2">
              Cada servicio genera su propio Magic Link apuntando a su URL configurada.
            </p>
          </div>

          {clavesServicios.map((srv) => {
            const countSrv = usuarios.filter((u) => u.servicios?.[srv.clave]).length;
            return (
              <div
                key={srv.clave}
                className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-white">{srv.nombre}</span>
                    <div className="flex items-center gap-1.5">
                      <code className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[11px]">
                        {srv.clave}
                      </code>
                      <button
                        onClick={() => setEditingService({ ...srv })}
                        title="Configurar URL del Magic Link de este servicio"
                        className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                      >
                        <Settings2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono truncate">
                    Magic Link base: <span className="text-teal-300">{srv.url_base}</span>
                    {srv.ruta_magic_link || '/acceso'}?token=...
                  </p>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-slate-400">
                    En vista: <strong className="text-white">{countSrv}</strong> habilitados
                  </span>
                  <button
                    onClick={() =>
                      setFilterServicio(filterServicio === srv.clave ? '' : srv.clave)
                    }
                    className={`text-xs px-2.5 py-1 rounded-md border transition ${
                      filterServicio === srv.clave
                        ? 'bg-indigo-600 text-white border-indigo-500'
                        : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    {filterServicio === srv.clave ? 'Quitar filtro' : 'Filtrar por clave'}
                  </button>
                </div>
              </div>
            );
          })}
        </section>

        {/* Barra de Filtros */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[240px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSkip(0);
                setSearch(e.target.value);
              }}
              placeholder="Buscar por nombre, email o PIN de 6 dígitos..."
              className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={filterServicio}
            onChange={(e) => {
              setSkip(0);
              setFilterServicio(e.target.value);
            }}
            className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Todos los servicios</option>
            {clavesServicios.map((s) => (
              <option key={s.clave} value={s.clave}>
                Con permiso en: {s.nombre} ({s.clave})
              </option>
            ))}
          </select>

          <select
            value={filterActivo}
            onChange={(e) => {
              setSkip(0);
              setFilterActivo(e.target.value);
            }}
            className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">Estado Global: Todos</option>
            <option value="true">Solo Cuentas Activas</option>
            <option value="false">Solo Suspendidas / Baja</option>
          </select>

          <button
            onClick={fetchUsuarios}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refrescar tabla"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </section>

        {/* Tabla Principal de Usuarios y Permisos por Servicio */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-[11px] uppercase tracking-wider text-slate-400">
                  <th className="py-3.5 px-4">ID / Usuario</th>
                  <th className="py-3.5 px-4">PIN (6 dígitos)</th>
                  <th className="py-3.5 px-4">
                    Servicios Habilitados (Clic para activar/desactivar)
                  </th>
                  <th className="py-3.5 px-4">Estado Global</th>
                  <th className="py-3.5 px-4 text-right">Magic Links y Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 text-sm">
                {usuarios.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 text-center text-slate-400">
                      {loading
                        ? 'Cargando cuentas desde MongoDB...'
                        : 'No se encontraron usuarios con los filtros seleccionados.'}
                    </td>
                  </tr>
                ) : (
                  usuarios.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2.5">
                          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            #{u.id}
                          </span>
                          <div>
                            <div className="font-semibold text-white flex items-center gap-1.5">
                              {u.name}
                              {u.tipoUsuario === 2 && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                  ADMIN
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400">{u.email}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-mono text-xs px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800 text-amber-300">
                          {u.codigoAcceso || '------'}
                        </span>
                      </td>

                      {/* Botones interactivos por cada servicio en el catálogo */}
                      <td className="py-3.5 px-4">
                        <div className="flex flex-wrap gap-2">
                          {clavesServicios.map((srv) => {
                            const isMasterAdmin = (u.tipoUsuario === 2 || u.email.toLowerCase() === 'admin@autenticador.com');
                            const tiene = isMasterAdmin ? true : Boolean(u.servicios?.[srv.clave]);
                            return (
                              <button
                                key={srv.clave}
                                disabled={isMasterAdmin}
                                onClick={() => !isMasterAdmin && handleToggleServicio(u.id, srv.clave)}
                                title={
                                  isMasterAdmin
                                    ? `Administrador Central: acceso permanente a ${srv.nombre}`
                                    : `Clic para ${
                                        tiene ? 'deshabilitar' : 'habilitar'
                                      } acceso a ${srv.nombre} (${srv.clave})`
                                }
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition ${
                                  isMasterAdmin
                                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 opacity-80 cursor-default'
                                    : tiene
                                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25'
                                    : 'bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700 hover:text-slate-300'
                                }`}
                              >
                                {tiene ? (
                                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                ) : (
                                  <XCircle className="w-3.5 h-3.5 text-slate-600" />
                                )}
                                <span>{srv.clave}</span>
                              </button>
                            );
                          })}
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        {(u.tipoUsuario === 2 || u.email.toLowerCase() === 'admin@autenticador.com') ? (
                          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg border border-emerald-500/40 text-emerald-300 bg-slate-950 select-none">
                            ACTIVO
                          </span>
                        ) : (
                          <select
                            value={u.estadoId}
                            onChange={(e) => handleCambiarEstado(u.id, Number(e.target.value))}
                            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border bg-slate-950 focus:outline-none ${
                              u.activo
                                ? 'border-emerald-500/40 text-emerald-300'
                                : 'border-rose-500/40 text-rose-300'
                            }`}
                          >
                            {estadosCatalogo.map((est) => (
                              <option key={est.id} value={est.id}>
                                {est.codigo}
                              </option>
                            ))}
                          </select>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleMagicLink(u)}
                            className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 transition"
                          >
                            <Link2 className="w-3.5 h-3.5" />
                            Magic Links
                          </button>

                          {(u.tipoUsuario === 2 || u.email.toLowerCase() === 'admin@autenticador.com') ? (
                            <span className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700 select-none">
                              Admin Protegido
                            </span>
                          ) : (
                            <button
                              onClick={() => handleEliminarUsuario(u)}
                              title="Eliminar permanentemente este usuario de la base de datos"
                              className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 flex items-center gap-1.5 transition"
                            >
                              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                              Eliminar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          <div className="px-4 py-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
            <span>
              Mostrando {usuarios.length} de {total} cuentas registradas
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - limit))}
                className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40 text-slate-200 hover:bg-slate-700"
              >
                Anterior
              </button>
              <button
                disabled={skip + limit >= total}
                onClick={() => setSkip(skip + limit)}
                className="px-3 py-1 rounded bg-slate-800 disabled:opacity-40 text-slate-200 hover:bg-slate-700"
              >
                Siguiente
              </button>
            </div>
          </div>
        </section>

        {/* Simulador en Vivo de Peticiones desde Contenedores Externos */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center gap-2.5 mb-3">
            <Terminal className="w-5 h-5 text-teal-400" />
            <div>
              <h2 className="text-sm font-bold text-white">
                Probador de Integración entre Contenedores (Endpoint{' '}
                <code className="text-teal-300">POST /auth/validar-acceso</code>)
              </h2>
              <p className="text-xs text-slate-400">
                Simulá la petición que realiza el backend de{' '}
                <code>mayoresactualizaciones</code> o <code>cognijuegos</code> al contenedor del
                Autenticador para validar si un usuario puede ingresar.
              </p>
            </div>
          </div>

          <form
            onSubmit={handleSimularValidacion}
            className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end"
          >
            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Email o PIN (6 dígitos) del Usuario
              </label>
              <input
                type="text"
                required
                value={simIdentifier}
                onChange={(e) => setSimIdentifier(e.target.value)}
                placeholder="marta.gonzalez@ejemplo.com o 123456"
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Clave del Servicio Solicitante
              </label>
              <select
                value={simServicio}
                onChange={(e) => setSimServicio(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
              >
                {clavesServicios.map((s) => (
                  <option key={s.clave} value={s.clave}>
                    {s.clave} ({s.nombre})
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={simLoading}
              className="py-2 px-4 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-semibold text-sm transition"
            >
              {simLoading ? 'Consultando Autenticador...' : 'Verificar Permiso de Ingreso'}
            </button>
          </form>

          {simResult && (
            <div
              className={`mt-4 p-4 rounded-xl border text-xs font-mono overflow-x-auto ${
                simResult.allowed
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                  : 'bg-rose-950/40 border-rose-500/40 text-rose-200'
              }`}
            >
              <div className="font-sans font-bold text-sm mb-2 flex items-center gap-2">
                {simResult.allowed ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )}
                <span>
                  Resultado: {simResult.allowed ? 'ACCESO AUTORIZADO' : 'ACCESO DENEGADO'} —{' '}
                  {simResult.message}
                </span>
              </div>
              <pre>{JSON.stringify(simResult, null, 2)}</pre>
            </div>
          )}
        </section>
      </main>

      {/* Modal Crear Nuevo Usuario */}
      {showNewUserModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">
              Registrar Usuario en Torre de Control
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Seleccioná qué servicios tendrá habilitados. Al crearlo se generarán los Magic Links
              de cada plataforma.
            </p>
            <form onSubmit={handleCreateUser} className="space-y-3.5">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Nombre Completo</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                  placeholder="Ej: Juan Pérez"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-300 mb-1">Correo Electrónico</label>
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                  placeholder="juan.perez@ejemplo.com"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-300 mb-1">
                    PIN 6 dígitos (Opcional)
                  </label>
                  <input
                    type="text"
                    value={newPin}
                    onChange={(e) => setNewPin(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                    placeholder="Autogenerado"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Rol</label>
                  <select
                    value={newTipo}
                    onChange={(e) => setNewTipo(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                  >
                    <option value={1}>1 - Usuario / Alumno</option>
                    <option value={2}>2 - Administrador</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1.5">
                  Servicios Habilitados (Claves)
                </label>
                <div className="space-y-2 bg-slate-950 p-3 rounded-lg border border-slate-800">
                  {clavesServicios.map((srv) => (
                    <label
                      key={srv.clave}
                      className="flex items-center justify-between text-xs cursor-pointer"
                    >
                      <span>
                        <strong className="text-slate-200">{srv.nombre}</strong>{' '}
                        <code className="text-indigo-300">({srv.clave})</code>
                      </span>
                      <input
                        type="checkbox"
                        checked={Boolean(newServicios[srv.clave])}
                        onChange={(e) =>
                          setNewServicios((prev) => ({
                            ...prev,
                            [srv.clave]: e.target.checked,
                          }))
                        }
                        className="rounded border-slate-700"
                      />
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewUserModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  Crear Cuenta y Generar Magic Links
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Registrar Nuevo Servicio en Catálogo */}
      {showNewServiceModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">
              Registrar Nueva Clave de Servicio
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Agregá un nuevo contenedor/servicio indicando su URL base para que genere su propio
              Magic Link independiente.
            </p>
            <form onSubmit={handleCreateService} className="space-y-3.5">
              <div>
                <label className="block text-xs text-slate-300 mb-1">
                  Clave identificadora (sin espacios)
                </label>
                <input
                  type="text"
                  required
                  value={srvClave}
                  onChange={(e) => setSrvClave(e.target.value)}
                  placeholder="ej: aulasvirtuales"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-300 mb-1">Nombre Visible</label>
                <input
                  type="text"
                  required
                  value={srvNombre}
                  onChange={(e) => setSrvNombre(e.target.value)}
                  placeholder="Ej: Aulas Virtuales"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="block text-xs text-slate-300 mb-1">
                    URL Base del Frontend
                  </label>
                  <input
                    type="url"
                    required
                    value={srvUrlBase}
                    onChange={(e) => setSrvUrlBase(e.target.value)}
                    placeholder="https://app.tudominio.com"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Ruta Magic Link</label>
                  <input
                    type="text"
                    required
                    value={srvRutaMagic}
                    onChange={(e) => setSrvRutaMagic(e.target.value)}
                    placeholder="/acceso"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-300 mb-1">Descripción</label>
                <input
                  type="text"
                  value={srvDesc}
                  onChange={(e) => setSrvDesc(e.target.value)}
                  placeholder="Contenedor de clases en vivo"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowNewServiceModal(false)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold"
                >
                  Guardar Servicio
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Editar URL de Servicio */}
      {editingService && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1">
              Configurar URL de Magic Link —{' '}
              <code className="text-indigo-300">{editingService.clave}</code>
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Definí a qué dominio/puerto y ruta redirigirá el Magic Link de este servicio.
            </p>
            <form onSubmit={handleUpdateServiceUrl} className="space-y-3.5">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Nombre Visible</label>
                <input
                  type="text"
                  required
                  value={editingService.nombre}
                  onChange={(e) =>
                    setEditingService({ ...editingService, nombre: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white"
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="block text-xs text-slate-300 mb-1">
                    URL Base del Servicio
                  </label>
                  <input
                    type="url"
                    required
                    value={editingService.url_base}
                    onChange={(e) =>
                      setEditingService({ ...editingService, url_base: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-300 mb-1">Ruta</label>
                  <input
                    type="text"
                    required
                    value={editingService.ruta_magic_link || '/acceso'}
                    onChange={(e) =>
                      setEditingService({
                        ...editingService,
                        ruta_magic_link: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-sm text-white font-mono"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingService(null)}
                  className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  Guardar Cambios
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Magic Links por Servicio */}
      {magicLinkData && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <div>
              <h3 className="text-lg font-bold text-white">
                Magic Links por Servicio y PIN — {magicLinkData.userName}
              </h3>
              <p className="text-xs text-slate-400">
                Cada enlace redirige directamente a la plataforma correspondiente (
                <code>/acceso?token=...</code>), valida contra el Autenticador e ingresa al inicio.
              </p>
            </div>

            <div className="space-y-3 text-xs">
              {/* PIN Compartido */}
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-slate-400 block">
                    PIN de 6 dígitos compartido (Código de Acceso):
                  </span>
                  <strong className="text-lg font-mono text-amber-300">
                    {magicLinkData.codigoAcceso}
                  </strong>
                </div>
                <button
                  onClick={() => copyText('pin', magicLinkData.codigoAcceso)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center gap-1.5 font-medium"
                >
                  {copiedField === 'pin' ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                  Copiar PIN
                </button>
              </div>

              {/* Un Magic Link distinto por cada servicio */}
              <div className="space-y-2.5">
                {magicLinkData.magicLinksList.map((ml) => (
                  <div
                    key={ml.clave}
                    className={`p-3.5 rounded-xl border space-y-2 ${
                      ml.habilitado
                        ? 'bg-slate-950 border-indigo-500/30'
                        : 'bg-slate-950/50 border-slate-800 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{ml.nombre}</span>
                        <code className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 text-[11px]">
                          {ml.clave}
                        </code>
                        {ml.habilitado ? (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            Permiso Activo
                          </span>
                        ) : (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 border border-rose-500/30">
                            Sin Permiso en este Servicio
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5">
                        <a
                          href={ml.accessUrl}
                          target="_blank"
                          rel="noreferrer"
                          title="Abrir enlace en pestaña nueva"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                        <button
                          onClick={() => copyText(`ml-${ml.clave}`, ml.accessUrl)}
                          className="px-2.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center gap-1"
                        >
                          {copiedField === `ml-${ml.clave}` ? (
                            <Check className="w-3.5 h-3.5" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                          Copiar Magic Link ({ml.clave})
                        </button>
                      </div>
                    </div>
                    <p className="font-mono text-[11px] text-teal-300 break-all bg-slate-900/90 p-2 rounded border border-slate-800">
                      {ml.accessUrl}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => setMagicLinkData(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


import React from 'react';
import { 
  Users, 
  UserPlus, 
  Search, 
  Shield, 
  MoreHorizontal, 
  CheckCircle,
  Lock,
  History
} from 'lucide-react';
import { UserRole } from '../types';

const UserManagement: React.FC = () => {
  const users = [
    { id: 1, name: 'Admin User', email: 'admin@nexus.io', role: UserRole.ADMIN, status: 'Active', lastLogin: '10 mins ago' },
    { id: 2, name: 'Data Eng 1', email: 'engineer@nexus.io', role: UserRole.DATA_ENGINEER, status: 'Active', lastLogin: '2 hours ago' },
    { id: 3, name: 'John Analyst', email: 'john@nexus.io', role: UserRole.ANALYST, status: 'Active', lastLogin: 'Yesterday' },
    { id: 4, name: 'Sarah Viewer', email: 'sarah@nexus.io', role: UserRole.VIEWER, status: 'Suspended', lastLogin: '3 days ago' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold">Team Members</h2>
          <p className="text-slate-500 text-sm">Manage user access and platform permissions</p>
        </div>
        <button className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-2xl font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">
          <UserPlus size={20} /> Add New User
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
             <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center gap-4">
                <div className="relative flex-1">
                  <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input 
                    type="text" 
                    placeholder="Search users..." 
                    className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                  />
                </div>
                <select className="bg-slate-50 border-none rounded-xl px-4 py-2 text-sm">
                  <option>All Roles</option>
                  <option>Admin</option>
                  <option>Engineer</option>
                </select>
             </div>
             <div className="overflow-x-auto">
               <table className="w-full text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/50">
                    <tr className="border-b border-slate-100 dark:border-slate-800">
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">User</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Role</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Status</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase">Last Login</th>
                      <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <img src={`https://picsum.photos/seed/${u.id}/32/32`} className="w-8 h-8 rounded-full" />
                            <div>
                              <p className="font-bold text-sm">{u.name}</p>
                              <p className="text-xs text-slate-500">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-1.5 text-xs font-bold text-slate-600 dark:text-slate-400">
                            <Shield size={14} className="text-blue-500" /> {u.role}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            u.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                          }`}>
                            {u.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-500">{u.lastLogin}</td>
                        <td className="px-6 py-4 text-right">
                          <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg text-slate-400">
                            <MoreHorizontal size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
               </table>
             </div>
          </div>
        </div>

        <div className="space-y-6">
           <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
             <div className="flex items-center gap-2 mb-4">
               <History size={18} className="text-blue-600" />
               <h4 className="font-bold">Audit Logs</h4>
             </div>
             <div className="space-y-4">
                {[
                  { action: 'Updated Policy', user: 'Admin', time: '2h ago' },
                  { action: 'Deleted Dataset', user: 'Data Eng 1', time: '5h ago' },
                  { action: 'Logged In', user: 'John Analyst', time: '6h ago' },
                ].map((log, i) => (
                  <div key={i} className="flex gap-3 text-xs">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1 flex-shrink-0" />
                    <div>
                      <p className="font-bold">{log.action}</p>
                      <p className="text-slate-500">{log.user} • {log.time}</p>
                    </div>
                  </div>
                ))}
             </div>
             <button className="mt-6 w-full py-2 bg-slate-50 dark:bg-slate-800 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-100 transition-colors">
                Full Audit History
             </button>
           </div>

           <div className="bg-gradient-to-br from-blue-600 to-indigo-700 p-6 rounded-2xl text-white shadow-xl shadow-blue-200">
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                <Lock size={20} />
              </div>
              <h4 className="font-bold text-lg mb-2">RBAC Control</h4>
              <p className="text-white/80 text-sm leading-relaxed mb-4">
                Enforce granular permissions based on organizational units. Standardized via LDAP/AD.
              </p>
              <button className="w-full py-2.5 bg-white text-blue-600 rounded-xl text-sm font-bold shadow-lg hover:bg-blue-50 transition-colors">
                Security Config
              </button>
           </div>
        </div>
      </div>
    </div>
  );
};

export default UserManagement;


import React from 'react';
import { PipelineStatus } from 'shared/types';

interface Props {
  status: PipelineStatus;
  activeStep: number;
}

const steps = [
  { name: 'API Sources', icon: 'fa-cloud-arrow-down', color: 'bg-blue-500' },
  { name: 'Data Lake (S3)', icon: 'fa-database', color: 'bg-indigo-500' },
  { name: 'Transformation (Spark)', icon: 'fa-bolt', color: 'bg-amber-500' },
  { name: 'Warehouse (Snowflake)', icon: 'fa-warehouse', color: 'bg-emerald-500' },
  { name: 'Dashboard', icon: 'fa-chart-line', color: 'bg-rose-500' }
];

const PipelineVisualizer: React.FC<Props> = ({ status, activeStep }) => {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-lg font-bold text-slate-800">Live Pipeline Flow</h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          status === PipelineStatus.PROCESSING ? 'bg-amber-100 text-amber-700 animate-pulse' :
          status === PipelineStatus.COMPLETED ? 'bg-emerald-100 text-emerald-700' :
          'bg-slate-100 text-slate-600'
        }`}>
          {status}
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between relative px-4">
        {/* Connection Line */}
        <div className="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-slate-100 -translate-y-1/2 z-0"></div>
        
        {steps.map((step, idx) => {
          const isActive = idx <= activeStep;
          const isCurrent = idx === activeStep && status !== PipelineStatus.IDLE;
          
          return (
            <div key={idx} className="flex flex-col items-center z-10 mb-8 md:mb-0">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 ${
                isActive ? step.color + ' text-white scale-110 shadow-lg' : 'bg-slate-100 text-slate-400'
              } ${isCurrent ? 'ring-4 ring-offset-2 ring-' + step.color.split('-')[1] + '-200 animate-bounce' : ''}`}>
                <i className={`fas ${step.icon} text-lg`}></i>
              </div>
              <span className={`mt-3 text-xs font-semibold ${isActive ? 'text-slate-800' : 'text-slate-400'}`}>
                {step.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineVisualizer;

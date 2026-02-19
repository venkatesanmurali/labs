export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6">
        <section className="bg-white p-6 rounded-lg border">
          <h2 className="font-medium mb-3">Drawing Standards</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Default Paper Size</label>
              <select className="w-full px-3 py-2 border rounded text-sm" defaultValue="ARCH_D">
                <option value="ARCH_D">ARCH D (24" x 36")</option>
                <option value="ARCH_E">ARCH E (36" x 48")</option>
                <option value="A1">A1 (594 x 841 mm)</option>
                <option value="A2">A2 (420 x 594 mm)</option>
                <option value="A3">A3 (297 x 420 mm)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Default Scale</label>
              <select className="w-full px-3 py-2 border rounded text-sm" defaultValue="1:100">
                <option>1:50</option>
                <option>1:100</option>
                <option>1:200</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Building Code</label>
              <select className="w-full px-3 py-2 border rounded text-sm" defaultValue="IBC">
                <option value="IBC">International Building Code (IBC)</option>
                <option value="NBC">National Building Code (NBC)</option>
              </select>
            </div>
          </div>
        </section>

        <section className="bg-white p-6 rounded-lg border">
          <h2 className="font-medium mb-3">Design Constraints</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Wall Thickness (m)</label>
              <input type="number" defaultValue={0.2} step={0.05} className="w-full px-3 py-2 border rounded text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Floor Height (m)</label>
              <input type="number" defaultValue={3.0} step={0.1} className="w-full px-3 py-2 border rounded text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Min Corridor Width (m)</label>
              <input type="number" defaultValue={1.2} step={0.1} className="w-full px-3 py-2 border rounded text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Door Width (m)</label>
              <input type="number" defaultValue={0.9} step={0.1} className="w-full px-3 py-2 border rounded text-sm" />
            </div>
          </div>
        </section>

        <section className="bg-white p-6 rounded-lg border">
          <h2 className="font-medium mb-3">CAD/BIM Adapter</h2>
          <p className="text-sm text-gray-500 mb-3">
            Select the backend adapter for generating construction documents.
          </p>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="adapter" value="native" defaultChecked className="text-primary-600" />
              <span className="text-sm">Native (ezdxf + ifcopenshell + reportlab)</span>
            </label>
            <label className="flex items-center gap-2 cursor-not-allowed opacity-50">
              <input type="radio" name="adapter" value="revit" disabled />
              <span className="text-sm">Revit / APS (Coming Soon)</span>
            </label>
            <label className="flex items-center gap-2 cursor-not-allowed opacity-50">
              <input type="radio" name="adapter" value="autocad" disabled />
              <span className="text-sm">AutoCAD (Coming Soon)</span>
            </label>
          </div>
        </section>
      </div>
    </div>
  )
}

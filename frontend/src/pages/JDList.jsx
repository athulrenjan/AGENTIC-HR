import { approveJD } from "../api/jdApi";

export default function JDList({ jds, onApprove }) {
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Job Descriptions</h2>

      {jds.map((jd) => (
        <div key={jd.jd_id} className="border p-4 mb-3">
          <p>
            <b>{jd.fields.title}</b> ({jd.fields.level})
          </p>
          <p>Status: {jd.status}</p>
          <div className="mt-2">
            <h4 className="font-semibold">Job Description:</h4>
            <pre className="whitespace-pre-wrap text-sm bg-gray-100 p-2 rounded">{jd.jd_text}</pre>
          </div>

          {jd.status === "DRAFT" && (
            <button
              className="mt-2 bg-green-600 text-white px-3 py-1"
              onClick={async () => {
                await approveJD(jd.jd_id);
                onApprove();
              }}
            >
              Approve & Lock
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

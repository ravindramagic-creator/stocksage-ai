import { useUpdateStats } from "../hooks/useUpdateStats";


export function UpdateStats() {

  const {
    data,
    isLoading,
  } = useUpdateStats();


  if (isLoading || !data) {
    return null;
  }


  const items = [
    {
      label: "All",
      value: data.total,
    },
    {
      label: "News",
      value:
        data.by_type.NEWS ?? 0,
    },
    {
      label: "Price",
      value:
        data.by_type.PRICE_MOVE ?? 0,
    },
    {
      label: "Dividend",
      value:
        data.by_type.DIVIDEND ?? 0,
    },
    {
      label: "Split",
      value:
        data.by_type.SPLIT ?? 0,
    },
  ];


  return (
    <div
      className="
        mb-4
        grid
        grid-cols-2
        gap-3
        md:grid-cols-5
      "
    >

      {items.map((item) => (

        <div
          key={item.label}
          className="
            rounded-xl
            border
            border-slate-800
            bg-slate-900
            p-4
          "
        >

          <div
            className="
              text-xs
              text-slate-500
            "
          >
            {item.label}
          </div>

          <div
            className="
              mt-1
              text-2xl
              font-bold
              text-white
            "
          >
            {item.value}
          </div>

        </div>

      ))}

    </div>
  );
}

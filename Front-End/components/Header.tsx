import NavItems from "@/components/NavItems";
import { searchStocks } from "@/lib/actions/finnhub.actions";

const Header = async () => {
    const initialStocks = await searchStocks();

    return (
        <header className="sticky top-0 header">
            <div className="container header-wrapper">
                <nav className="hidden sm:block">
                    <NavItems initialStocks={initialStocks} />
                </nav>
            </div>
        </header>
    )
}
export default Header

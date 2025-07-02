async function loadIdsData () {
    try {
        // 使用fetch API获取ids.json文件内容
        const response = await fetch( './ids.json' );
        if ( !response.ok ) {
            throw new Error( `HTTP错误! 状态码: ${ response.status }` );
        }
        // 解析JSON数据
        const idsData = await response.json();
        return idsData;
    } catch ( error ) {
        console.error( '加载ids.json文件出错：', error );
        throw error; // 重新抛出错误，让调用者知道发生了错误
    }
}
let idsObj = [];
// 使用示例
loadIdsData().then( ( idsData ) => {
    // 将ids数据转换为对象，方便查询
    idsObj = idsData.reduce( ( acc, [ char, components ] ) => {
        acc[ char ] = components.join( ' ' );
        return acc;
    }, {} );
    window.idsObj = idsObj;
} ).catch( error => {
    console.error( '处理ids.json数据时出错：', error );
} );// ids.json 数据

// 暴露接口FindChineseComponent
function FindChineseComponent ( char ) {
    // 截取字符串里的第一个字符
    const firstChar = char;
    // 使用Set来存储字符，确保唯一性
    const resultSet = new Set( [ firstChar ] );

    // 查询字符是否在ids中有记录
    if ( idsObj.hasOwnProperty( firstChar ) ) {
        // 遍历每个component字符串
        for ( const c of Array.from( idsObj[ firstChar ] ) ) {
            if ( c === ' ' ) break;
            resultSet.add( c );
        }
    }
    return resultSet;
}
// 新增接口FindCharactersWithComponent
function FindCharactersWithComponent ( componentChar, range, result ) {
    //console.log( componentChar, range );
    // 初始化结果数组
    result.add( componentChar );
    // 遍历idsObj中的所有字符及其component数组
    for ( let char of range ) {
        let components = idsObj[ char ];
        if ( components ) { // 确保组件存在
            // 检查输入的字符是否存在于某个component中
            if ( components.includes( componentChar ) ) {
                // 如果存在，则将对应的字符添加到结果数组中
                result.add( char );
            }
        }
    }

    // 返回结果数组
    return result;
}
window.FindCharactersWithComponent = FindCharactersWithComponent;
window.FindChineseComponent = FindChineseComponent;
export { FindChineseComponent, FindCharactersWithComponent };